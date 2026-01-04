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
    """Create the order and generate QRIS payment."""
    from orders.models import OrderStatus
    
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
    
    # Create order with awaiting_payment status
    order_data = user.conversation_data
    order = await sync_to_async(Order.objects.create)(
        user=user,
        delivery_address=order_data.get('address', ''),
        phone=order_data.get('phone', ''),
        notes=order_data.get('notes', ''),
        total=total,
        status=OrderStatus.PENDING
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
    
    # Generate QRIS payment
    from payments.services import midtrans_service
    
    # Need to refetch order with items for QRIS generation
    order_with_items = await sync_to_async(
        lambda: Order.objects.prefetch_related('items').get(id=order.id)
    )()
    
    payment_result = await sync_to_async(midtrans_service.create_qris_payment)(order_with_items)
    
    if payment_result['success']:
        # Format rupiah
        def format_rupiah(amount):
            return f"Rp {int(amount):,}".replace(',', '.')
        
        # Build items summary
        items_text = ""
        for item in cart_items:
            subtotal = item.menu_item.price * item.quantity
            items_text += f"• {item.quantity}x {item.menu_item.name} - {format_rupiah(subtotal)}\n"
        
        # Send QR code message with payment instructions
        message = f"""
🧾 <b>Order #{order.order_number}</b>

{items_text}
<b>Total: {format_rupiah(total)}</b>

📱 <b>Scan the QR code below to pay</b>
Use GoPay, OVO, DANA, ShopeePay, or any QRIS-compatible app.

⏰ Payment expires in <b>15 minutes</b>

📍 Delivery to: {order.delivery_address}
"""
        await telegram_service.send_message(chat_id, message)
        
        # Send QR code image
        qr_url = payment_result.get('qr_url')
        if qr_url:
            await telegram_service.send_photo(chat_id, qr_url, "Scan to pay with QRIS")
        else:
            # If no image URL, send the QR string
            qr_string = payment_result.get('qr_string', '')
            await telegram_service.send_message(
                chat_id, 
                f"<code>{qr_string}</code>\n\n(Copy this QR string if image doesn't load)"
            )
    else:
        # Payment creation failed, notify user
        await telegram_service.send_message(
            chat_id,
            f"❌ Sorry, there was an error creating your payment: {payment_result.get('error')}\n\n"
            "Your order has been saved. Please try again or contact support."
        )
    
    # Notify dashboard via WebSocket (order created, awaiting payment)
    from channels.layers import get_channel_layer
    
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

