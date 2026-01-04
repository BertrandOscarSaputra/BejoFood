"""
Callback query handlers for Telegram bot.
Handles button clicks from inline keyboards.
"""
from typing import Dict, Any
from asgiref.sync import sync_to_async

from orders.models import TelegramUser, Cart, CartItem
from menu.models import Category, MenuItem
from core.services.telegram import telegram_service


async def handle_callback_query(update: Dict[str, Any]) -> None:
    """Route callback queries to appropriate handlers."""
    callback = update.get('callback_query', {})
    data = callback.get('data', '')
    callback_id = callback.get('id')
    user_data = callback.get('from', {})
    chat_id = str(callback.get('message', {}).get('chat', {}).get('id'))
    
    # Parse callback data
    parts = data.split(':')
    action = parts[0] if parts else ''
    
    # Route to handler
    try:
        if action == 'category':
            await handle_category_select(chat_id, user_data, parts[1] if len(parts) > 1 else '')
        elif action == 'add':
            await handle_add_to_cart(chat_id, user_data, parts[1] if len(parts) > 1 else '')
        elif action == 'menu':
            await handle_menu_back(chat_id)
        elif action == 'cart':
            await handle_cart_action(chat_id, user_data, parts[1:])
        elif action == 'checkout':
            await handle_checkout_action(chat_id, user_data, parts[1] if len(parts) > 1 else '')
        elif action == 'noop':
            pass  # Do nothing
        
        # Answer callback to remove loading state
        await telegram_service.answer_callback(callback_id)
    except Exception as e:
        await telegram_service.answer_callback(callback_id, f"Error: {str(e)}")


async def handle_category_select(chat_id: str, user_data: Dict, category_id: str) -> None:
    """Handle category selection - show items in category."""
    try:
        category = await sync_to_async(Category.objects.get)(id=int(category_id))
    except Category.DoesNotExist:
        await telegram_service.send_message(chat_id, "Category not found.")
        return
    
    items = await sync_to_async(list)(
        MenuItem.objects.filter(
            category=category,
            is_available=True
        ).values('id', 'name', 'description', 'price')
    )
    
    items_data = [
        {
            'id': item['id'],
            'name': item['name'],
            'description': item['description'],
            'price': float(item['price'])
        }
        for item in items
    ]
    
    category_name = f"{category.emoji} {category.name}" if category.emoji else category.name
    await telegram_service.send_items(chat_id, category_name, items_data)


async def handle_add_to_cart(chat_id: str, user_data: Dict, item_id: str) -> None:
    """Handle adding item to cart."""
    # Get user
    try:
        user = await sync_to_async(TelegramUser.objects.get)(
            telegram_id=user_data.get('id')
        )
    except TelegramUser.DoesNotExist:
        await telegram_service.send_message(chat_id, "Please use /start first!")
        return
    
    # Get or create cart
    cart, _ = await sync_to_async(Cart.objects.get_or_create)(user=user)
    
    # Get menu item
    try:
        menu_item = await sync_to_async(MenuItem.objects.get)(id=int(item_id))
    except MenuItem.DoesNotExist:
        await telegram_service.send_message(chat_id, "Item not found.")
        return
    
    # Add to cart or increment quantity
    cart_item, created = await sync_to_async(CartItem.objects.get_or_create)(
        cart=cart,
        menu_item=menu_item,
        defaults={'quantity': 1}
    )
    
    if not created:
        cart_item.quantity += 1
        await sync_to_async(cart_item.save)()
    
    total = await sync_to_async(lambda: cart.total)()
    item_count = await sync_to_async(lambda: cart.item_count)()
    
    await telegram_service.send_message(
        chat_id,
        f"✅ Added <b>{menu_item.name}</b> to cart!\n\n"
        f"🛒 Cart: {item_count} items - Rp {int(total):,}\n\n".replace(',', '.') +
        f"Use /cart to view or /menu to continue shopping."
    )


async def handle_menu_back(chat_id: str) -> None:
    """Handle back to menu button."""
    categories = await sync_to_async(list)(
        Category.objects.filter(is_active=True).order_by('order', 'name').values('id', 'name', 'emoji')
    )
    await telegram_service.send_menu(chat_id, categories)


async def handle_cart_action(chat_id: str, user_data: Dict, action_parts: list) -> None:
    """Handle cart-related actions."""
    if not action_parts:
        return
    
    action = action_parts[0]
    
    # Get user and cart
    try:
        user = await sync_to_async(TelegramUser.objects.get)(
            telegram_id=user_data.get('id')
        )
        cart = await sync_to_async(lambda: user.cart)()
    except (TelegramUser.DoesNotExist, Cart.DoesNotExist):
        await telegram_service.send_message(chat_id, "Please use /start first!")
        return
    
    if action == 'view':
        # Show cart
        cart_items = await sync_to_async(list)(
            cart.items.select_related('menu_item').all()
        )
        items_data = [
            {
                'id': item.id,
                'name': item.menu_item.name,
                'price': float(item.menu_item.price),
                'quantity': item.quantity
            }
            for item in cart_items
        ]
        total = sum(item['price'] * item['quantity'] for item in items_data)
        await telegram_service.send_cart(chat_id, items_data, total)
    
    elif action == 'clear':
        await sync_to_async(cart.clear)()
        await telegram_service.send_message(
            chat_id,
            "🗑️ Cart cleared!\n\nUse /menu to start shopping again."
        )
    
    elif action == 'increase' and len(action_parts) > 1:
        item_id = action_parts[1]
        try:
            cart_item = await sync_to_async(CartItem.objects.get)(id=int(item_id))
            cart_item.quantity += 1
            await sync_to_async(cart_item.save)()
            await refresh_cart_display(chat_id, cart)
        except CartItem.DoesNotExist:
            pass
    
    elif action == 'decrease' and len(action_parts) > 1:
        item_id = action_parts[1]
        try:
            cart_item = await sync_to_async(CartItem.objects.get)(id=int(item_id))
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                await sync_to_async(cart_item.save)()
            else:
                await sync_to_async(cart_item.delete)()
            await refresh_cart_display(chat_id, cart)
        except CartItem.DoesNotExist:
            pass
    
    elif action == 'remove' and len(action_parts) > 1:
        item_id = action_parts[1]
        try:
            cart_item = await sync_to_async(CartItem.objects.get)(id=int(item_id))
            await sync_to_async(cart_item.delete)()
            await refresh_cart_display(chat_id, cart)
        except CartItem.DoesNotExist:
            pass


async def refresh_cart_display(chat_id: str, cart: Cart) -> None:
    """Refresh cart display after modification."""
    cart_items = await sync_to_async(list)(
        cart.items.select_related('menu_item').all()
    )
    items_data = [
        {
            'id': item.id,
            'name': item.menu_item.name,
            'price': float(item.menu_item.price),
            'quantity': item.quantity
        }
        for item in cart_items
    ]
    total = sum(item['price'] * item['quantity'] for item in items_data)
    await telegram_service.send_cart(chat_id, items_data, total)


async def handle_checkout_action(chat_id: str, user_data: Dict, action: str) -> None:
    """Handle checkout-related actions."""
    if action == 'start':
        # Get user
        try:
            user = await sync_to_async(TelegramUser.objects.get)(
                telegram_id=user_data.get('id')
            )
            cart = await sync_to_async(lambda: user.cart)()
        except (TelegramUser.DoesNotExist, Cart.DoesNotExist):
            await telegram_service.send_message(chat_id, "Please use /start first!")
            return
        
        # Check if cart has items
        item_count = await sync_to_async(lambda: cart.item_count)()
        if item_count == 0:
            await telegram_service.send_message(
                chat_id,
                "🛒 Your cart is empty! Use /menu to add some items first."
            )
            return
        
        # Set conversation state
        user.conversation_state = 'checkout_address'
        user.conversation_data = {}
        await sync_to_async(user.save)()
        
        await telegram_service.send_message(
            chat_id,
            "📍 <b>Checkout</b>\n\nPlease enter your <b>delivery address</b>:"
        )
