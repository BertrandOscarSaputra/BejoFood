"""
Conversation handlers for multi-step flows (checkout).
"""
from typing import Dict, Any
from asgiref.sync import sync_to_async
from decimal import Decimal

from orders.models import TelegramUser, Order, OrderItem
from core.services.telegram import telegram_service


async def handle_conversation(update: Dict[str, Any]) -> bool:
    """
    Handle conversation states for multi-step flows.
    Returns True if message was handled, False otherwise.
    """
    message = update.get('message', {})
    text = message.get('text', '')
    user_data = message.get('from', {})
    chat_id = str(message.get('chat', {}).get('id'))
    
    # Get user
    try:
        user = await sync_to_async(TelegramUser.objects.get)(
            telegram_id=user_data.get('id')
        )
    except TelegramUser.DoesNotExist:
        return False
    
    # Check conversation state
    state = user.conversation_state
    if not state:
        return False
    
    # Route based on state
    if state == 'checkout_address':
        await handle_checkout_address(user, chat_id, text)
        return True
    elif state == 'checkout_phone':
        await handle_checkout_phone(user, chat_id, text)
        return True
    elif state == 'checkout_notes':
        await handle_checkout_notes(user, chat_id, text)
        return True
    
    return False


async def handle_checkout_address(user: TelegramUser, chat_id: str, address: str) -> None:
    """Handle delivery address input."""
    if not address or len(address) < 10:
        await telegram_service.send_message(
            chat_id,
            "⚠️ Please enter a valid address (at least 10 characters)."
        )
        return
    
    # Store address and move to next step
    user.conversation_data['address'] = address
    user.conversation_state = 'checkout_phone'
    await sync_to_async(user.save)()
    
    await telegram_service.send_message(
        chat_id,
        "📞 Great! Now please enter your <b>phone number</b>:"
    )


async def handle_checkout_phone(user: TelegramUser, chat_id: str, phone: str) -> None:
    """Handle phone number input."""
    # Simple phone validation
    phone_clean = ''.join(c for c in phone if c.isdigit() or c == '+')
    if len(phone_clean) < 10:
        await telegram_service.send_message(
            chat_id,
            "⚠️ Please enter a valid phone number (at least 10 digits)."
        )
        return
    
    # Store phone and move to notes step
    user.conversation_data['phone'] = phone_clean
    user.conversation_state = 'checkout_notes'
    await sync_to_async(user.save)()
    
    keyboard = {
        "inline_keyboard": [[
            {"text": "Skip", "callback_data": "checkout:skip_notes"}
        ]]
    }
    
    await telegram_service.send_message(
        chat_id,
        "📝 Any special instructions? (or tap Skip)\n\nExample: Extra sauce, no onions, etc.",
        keyboard
    )


async def handle_checkout_notes(user: TelegramUser, chat_id: str, notes: str) -> None:
    """Handle notes input and finalize order."""
    user.conversation_data['notes'] = notes
    await finalize_order(user, chat_id)


async def finalize_order(user: TelegramUser, chat_id: str) -> None:
    """Create the order from cart."""
    # Get cart
    cart = await sync_to_async(lambda: user.cart)()
    cart_items = await sync_to_async(list)(
        cart.items.select_related('menu_item').all()
    )
    
    if not cart_items:
        user.conversation_state = ''
        user.conversation_data = {}
        await sync_to_async(user.save)()
        await telegram_service.send_message(
            chat_id,
            "🛒 Your cart is empty!"
        )
        return
    
    # Calculate total
    total = sum(
        item.menu_item.price * item.quantity 
        for item in cart_items
    )
    
    # Create order
    order_data = user.conversation_data
    order = await sync_to_async(Order.objects.create)(
        user=user,
        delivery_address=order_data.get('address', ''),
        phone=order_data.get('phone', ''),
        notes=order_data.get('notes', ''),
        total=total
    )
    
    # Create order items
    order_items = []
    for cart_item in cart_items:
        order_item = OrderItem(
            order=order,
            menu_item=cart_item.menu_item,
            name=cart_item.menu_item.name,
            quantity=cart_item.quantity,
            price=cart_item.menu_item.price
        )
        order_items.append(order_item)
    
    await sync_to_async(OrderItem.objects.bulk_create)(order_items)
    
    # Clear cart
    await sync_to_async(cart.clear)()
    
    # Clear conversation state
    user.conversation_state = ''
    user.conversation_data = {}
    await sync_to_async(user.save)()
    
    # Send confirmation
    items_summary = [
        {
            'name': item.menu_item.name,
            'quantity': item.quantity,
            'subtotal': float(item.menu_item.price * item.quantity)
        }
        for item in cart_items
    ]
    
    await telegram_service.send_order_confirmation(
        chat_id,
        {
            'order_number': order.order_number,
            'items': items_summary,
            'total': float(total),
            'delivery_address': order.delivery_address,
            'phone': order.phone
        }
    )
    
    # Notify dashboard via WebSocket
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    if channel_layer:
        await channel_layer.group_send(
            'orders',
            {
                'type': 'order_update',
                'data': {
                    'action': 'new_order',
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'total': float(total),
                    'status': order.status
                }
            }
        )
