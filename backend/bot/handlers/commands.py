"""
Command handlers for Telegram bot.
Handles: /start, /menu, /cart, /checkout, /status, /help
"""
from typing import Dict, Any
from asgiref.sync import sync_to_async

from orders.models import TelegramUser, Cart, Order, OrderStatus
from menu.models import Category
from core.services.telegram import telegram_service


async def handle_start(update: Dict[str, Any]) -> None:
    """Handle /start command - Welcome and register user."""
    message = update.get('message', {})
    user_data = message.get('from', {})
    chat_id = str(message.get('chat', {}).get('id'))
    
    # Get or create user
    user, created = await sync_to_async(TelegramUser.objects.get_or_create)(
        telegram_id=user_data.get('id'),
        defaults={
            'username': user_data.get('username', ''),
            'first_name': user_data.get('first_name', 'User'),
            'last_name': user_data.get('last_name', '')
        }
    )
    
    # Create cart if doesn't exist
    await sync_to_async(Cart.objects.get_or_create)(user=user)
    
    welcome_text = f"""
👋 <b>Welcome to BejoFood, {user.first_name}!</b>

I'm your food ordering assistant. Here's what you can do:

📋 /menu - Browse our delicious menu
🛒 /cart - View your shopping cart
💳 /checkout - Complete your order
📦 /status - Check your order status
❓ /help - Get help

<b>Ready to order? Tap /menu to get started!</b>
"""
    await telegram_service.send_message(chat_id, welcome_text)


async def handle_menu(update: Dict[str, Any]) -> None:
    """Handle /menu command - Show menu categories."""
    message = update.get('message', {})
    chat_id = str(message.get('chat', {}).get('id'))
    
    # Get active categories
    categories = await sync_to_async(list)(
        Category.objects.filter(is_active=True).order_by('order', 'name').values('id', 'name', 'emoji')
    )
    
    if not categories:
        await telegram_service.send_message(
            chat_id,
            "😔 Sorry, our menu is currently empty. Please check back later!"
        )
        return
    
    await telegram_service.send_menu(chat_id, categories)


async def handle_cart(update: Dict[str, Any]) -> None:
    """Handle /cart command - Show cart contents."""
    message = update.get('message', {})
    user_data = message.get('from', {})
    chat_id = str(message.get('chat', {}).get('id'))
    
    # Get user and cart
    try:
        user = await sync_to_async(TelegramUser.objects.get)(
            telegram_id=user_data.get('id')
        )
        cart = await sync_to_async(lambda: user.cart)()
    except TelegramUser.DoesNotExist:
        await telegram_service.send_message(
            chat_id,
            "Please use /start first to begin ordering!"
        )
        return
    except Cart.DoesNotExist:
        cart = await sync_to_async(Cart.objects.create)(user=user)
    
    # Get cart items
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


async def handle_checkout(update: Dict[str, Any]) -> None:
    """Handle /checkout command - Start checkout process."""
    message = update.get('message', {})
    user_data = message.get('from', {})
    chat_id = str(message.get('chat', {}).get('id'))
    
    # Get user and cart
    try:
        user = await sync_to_async(TelegramUser.objects.get)(
            telegram_id=user_data.get('id')
        )
        cart = await sync_to_async(lambda: user.cart)()
    except (TelegramUser.DoesNotExist, Cart.DoesNotExist):
        await telegram_service.send_message(
            chat_id,
            "Please use /start first to begin ordering!"
        )
        return
    
    # Check if cart has items
    item_count = await sync_to_async(lambda: cart.item_count)()
    
    if item_count == 0:
        await telegram_service.send_message(
            chat_id,
            "🛒 Your cart is empty! Use /menu to add some items first."
        )
        return
    
    # Set conversation state to collect delivery info
    user.conversation_state = 'checkout_address'
    user.conversation_data = {}
    await sync_to_async(user.save)()
    
    await telegram_service.send_message(
        chat_id,
        "📍 <b>Checkout</b>\n\nPlease enter your <b>delivery address</b>:"
    )


async def handle_status(update: Dict[str, Any]) -> None:
    """Handle /status command - Show recent order status."""
    message = update.get('message', {})
    user_data = message.get('from', {})
    chat_id = str(message.get('chat', {}).get('id'))
    
    try:
        user = await sync_to_async(TelegramUser.objects.get)(
            telegram_id=user_data.get('id')
        )
    except TelegramUser.DoesNotExist:
        await telegram_service.send_message(
            chat_id,
            "Please use /start first!"
        )
        return
    
    # Get recent orders
    orders = await sync_to_async(list)(
        Order.objects.filter(user=user).order_by('-created_at')[:5]
    )
    
    if not orders:
        await telegram_service.send_message(
            chat_id,
            "📦 You don't have any orders yet.\n\nUse /menu to place your first order!"
        )
        return
    
    status_icons = {
        'pending': '⏳',
        'confirmed': '✅',
        'preparing': '👨‍🍳',
        'ready': '🎉',
        'completed': '✅',
        'cancelled': '❌'
    }
    
    text = "📦 <b>Your Recent Orders</b>\n\n"
    for order in orders:
        icon = status_icons.get(order.status, '📦')
        text += f"{icon} <b>#{order.order_number}</b>\n"
        text += f"   Status: {order.get_status_display()}\n"
        text += f"   Total: ₱{order.total}\n"
        text += f"   Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    await telegram_service.send_message(chat_id, text)


async def handle_help(update: Dict[str, Any]) -> None:
    """Handle /help command - Show help message."""
    message = update.get('message', {})
    chat_id = str(message.get('chat', {}).get('id'))
    
    help_text = """
❓ <b>BejoFood Help</b>

<b>Available Commands:</b>

/start - Start the bot and register
/menu - Browse our food menu
/cart - View your shopping cart
/checkout - Complete your order
/status - Check order status
/help - Show this help message

<b>How to Order:</b>
1️⃣ Use /menu to browse categories
2️⃣ Tap a category to see items
3️⃣ Tap an item to add to cart
4️⃣ Use /cart to review your order
5️⃣ Use /checkout to complete

Need assistance? Contact us at support@bejofood.com
"""
    await telegram_service.send_message(chat_id, help_text)


# Command router
COMMAND_HANDLERS = {
    '/start': handle_start,
    '/menu': handle_menu,
    '/cart': handle_cart,
    '/checkout': handle_checkout,
    '/status': handle_status,
    '/help': handle_help,
}


async def route_command(update: Dict[str, Any]) -> bool:
    """Route command to appropriate handler. Returns True if handled."""
    message = update.get('message', {})
    text = message.get('text', '')
    
    # Extract command (first word)
    command = text.split()[0].lower() if text else ''
    
    # Remove @botname if present
    if '@' in command:
        command = command.split('@')[0]
    
    handler = COMMAND_HANDLERS.get(command)
    if handler:
        await handler(update)
        return True
    
    return False
