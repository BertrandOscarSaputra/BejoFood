"""
Telegram webhook handler.
"""
import json
import logging

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from asgiref.sync import async_to_sync

from .handlers.commands import route_command
from .handlers.callbacks import handle_callback_query
from .handlers.conversation import handle_conversation

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """
    Handle incoming Telegram webhook requests.
    Routes to appropriate handler based on update type.
    """
    try:
        # Parse incoming update
        update = json.loads(request.body)
        logger.info(f"Received update: {update}")
        
        # Process asynchronously
        async_to_sync(process_update)(update)
        
        return JsonResponse({'ok': True})
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
    
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        # Return 200 to acknowledge receipt (prevent Telegram retries)
        return JsonResponse({'ok': True})


async def process_update(update: dict) -> None:
    """Process a Telegram update asynchronously."""
    
    # Handle callback queries (button clicks)
    if 'callback_query' in update:
        # Special handling for skip notes
        callback_data = update['callback_query'].get('data', '')
        if callback_data == 'checkout:skip_notes':
            await handle_skip_notes(update)
        else:
            await handle_callback_query(update)
        return
    
    # Handle messages
    if 'message' in update:
        message = update['message']
        text = message.get('text', '')
        
        # Skip if no text
        if not text:
            return
        
        # Check if it's a command
        if text.startswith('/'):
            handled = await route_command(update)
            if handled:
                return
        
        # Check for conversation state (multi-step flows)
        handled = await handle_conversation(update)
        if handled:
            return
        
        # Default response for unhandled messages
        from core.services.telegram import telegram_service
        chat_id = str(message.get('chat', {}).get('id'))
        await telegram_service.send_message(
            chat_id,
            "I didn't understand that. Use /help to see available commands."
        )


async def handle_skip_notes(update: dict) -> None:
    """Handle skipping notes during checkout."""
    from orders.models import TelegramUser
    from asgiref.sync import sync_to_async
    from .handlers.conversation import finalize_order
    from core.services.telegram import telegram_service
    
    callback = update.get('callback_query', {})
    user_data = callback.get('from', {})
    chat_id = str(callback.get('message', {}).get('chat', {}).get('id'))
    callback_id = callback.get('id')
    
    try:
        user = await sync_to_async(TelegramUser.objects.get)(
            telegram_id=user_data.get('id')
        )
        
        if user.conversation_state == 'checkout_notes':
            user.conversation_data['notes'] = ''
            await finalize_order(user, chat_id)
        
        await telegram_service.answer_callback(callback_id)
    except TelegramUser.DoesNotExist:
        await telegram_service.answer_callback(callback_id, "Please use /start first!")
