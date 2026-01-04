"""
Midtrans webhook endpoint for payment notifications.
"""
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .services import midtrans_service
from core.services.telegram import telegram_service

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def midtrans_webhook(request):
    """
    Receive payment notifications from Midtrans.
    Updates payment status and notifies user via Telegram.
    """
    try:
        notification = json.loads(request.body)
        logger.info(f"Midtrans notification received: {notification}")
        
        transaction_status = notification.get('transaction_status')
        transaction_id = notification.get('transaction_id')
        
        # Process the notification
        success, message = midtrans_service.handle_notification(notification)
        
        if success:
            # If payment was successful, notify the customer
            if transaction_status == 'settlement':
                async_to_sync(notify_payment_success)(transaction_id)
            elif transaction_status == 'expire':
                async_to_sync(notify_payment_expired)(transaction_id)
            
            # Broadcast to dashboard
            broadcast_order_update(transaction_id, transaction_status)
        
        return JsonResponse({'status': 'ok', 'message': message})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in Midtrans webhook")
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.exception(f"Error processing Midtrans webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


async def notify_payment_success(transaction_id):
    """Send Telegram notification on successful payment."""
    from .models import Payment
    from asgiref.sync import sync_to_async
    
    try:
        payment = await sync_to_async(
            lambda: Payment.objects.select_related('order', 'order__user').get(transaction_id=transaction_id)
        )()
        
        order = payment.order
        user = order.user
        chat_id = str(user.telegram_id)
        
        # Format rupiah
        def format_rupiah(amount):
            return f"Rp {int(amount):,}".replace(',', '.')
        
        message = f"""
✅ <b>Payment Received!</b>

📝 <b>Order #{order.order_number}</b>
💰 Amount: {format_rupiah(payment.gross_amount)}

Your order has been <b>confirmed</b> and is being prepared! 🍳

Use /status to track your order.
"""
        await telegram_service.send_message(chat_id, message)
        
    except Exception as e:
        logger.exception(f"Error notifying payment success: {e}")


async def notify_payment_expired(transaction_id):
    """Send Telegram notification when payment expires."""
    from .models import Payment
    from asgiref.sync import sync_to_async
    
    try:
        payment = await sync_to_async(
            lambda: Payment.objects.select_related('order', 'order__user').get(transaction_id=transaction_id)
        )()
        
        order = payment.order
        user = order.user
        chat_id = str(user.telegram_id)
        
        message = f"""
⏰ <b>Payment Expired</b>

Your payment for <b>Order #{order.order_number}</b> has expired.

Would you like to place a new order? Use /menu to start again.
"""
        await telegram_service.send_message(chat_id, message)
        
    except Exception as e:
        logger.exception(f"Error notifying payment expired: {e}")


def broadcast_order_update(transaction_id, status):
    """Broadcast order update to dashboard via WebSocket."""
    try:
        from .models import Payment
        payment = Payment.objects.select_related('order').get(transaction_id=transaction_id)
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'orders',
            {
                'type': 'order_update',
                'data': {
                    'action': 'payment_update',
                    'order_id': payment.order.id,
                    'order_number': payment.order.order_number,
                    'payment_status': status,
                    'order_status': payment.order.status
                }
            }
        )
    except Exception as e:
        logger.exception(f"Error broadcasting order update: {e}")
