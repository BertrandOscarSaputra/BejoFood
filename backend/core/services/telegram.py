"""
Telegram implementation of the messaging service.
"""
import httpx
from typing import Optional, List, Dict, Any
from django.conf import settings

from .messaging import MessagingService


class TelegramService(MessagingService):
    """
    Telegram Bot API implementation of MessagingService.
    Uses httpx for async HTTP requests.
    """

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def _make_request(self, method: str, data: Dict) -> Dict:
        """Make an async request to Telegram API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{method}",
                json=data,
                timeout=30.0
            )
            return response.json()

    def _build_inline_keyboard(self, buttons: List[List[Dict]]) -> Dict:
        """Build inline keyboard markup."""
        return {"inline_keyboard": buttons}

    async def send_message(
        self,
        user_id: str,
        text: str,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """Send a text message to a user."""
        data = {
            "chat_id": user_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        result = await self._make_request("sendMessage", data)
        return result.get("ok", False)

    async def send_menu(
        self,
        user_id: str,
        categories: List[Dict]
    ) -> bool:
        """Send menu categories as inline buttons."""
        keyboard = []
        for cat in categories:
            keyboard.append([{
                "text": f"{cat.get('emoji', '📋')} {cat['name']}",
                "callback_data": f"category:{cat['id']}"
            }])
        
        # Add cart button at bottom
        keyboard.append([{
            "text": "🛒 View Cart",
            "callback_data": "cart:view"
        }])

        text = "🍽️ <b>Our Menu</b>\n\nSelect a category to browse:"
        return await self.send_message(
            user_id,
            text,
            self._build_inline_keyboard(keyboard)
        )

    async def send_items(
        self,
        user_id: str,
        category_name: str,
        items: List[Dict]
    ) -> bool:
        """Send menu items for a category."""
        if not items:
            text = f"<b>{category_name}</b>\n\nNo items available in this category."
            keyboard = [[{"text": "⬅️ Back to Menu", "callback_data": "menu:back"}]]
            return await self.send_message(user_id, text, self._build_inline_keyboard(keyboard))

        text = f"<b>{category_name}</b>\n\n"
        keyboard = []
        
        for item in items:
            text += f"• <b>{item['name']}</b> - ₱{item['price']}\n"
            if item.get('description'):
                text += f"  <i>{item['description']}</i>\n"
            text += "\n"
            
            keyboard.append([{
                "text": f"➕ {item['name']} - ₱{item['price']}",
                "callback_data": f"add:{item['id']}"
            }])

        keyboard.append([{"text": "⬅️ Back to Menu", "callback_data": "menu:back"}])
        keyboard.append([{"text": "🛒 View Cart", "callback_data": "cart:view"}])

        return await self.send_message(
            user_id,
            text,
            self._build_inline_keyboard(keyboard)
        )

    async def send_cart(
        self,
        user_id: str,
        cart_items: List[Dict],
        total: float
    ) -> bool:
        """Send cart contents."""
        if not cart_items:
            text = "🛒 <b>Your Cart is Empty</b>\n\nUse /menu to browse our menu!"
            keyboard = [[{"text": "📋 View Menu", "callback_data": "menu:back"}]]
            return await self.send_message(user_id, text, self._build_inline_keyboard(keyboard))

        text = "🛒 <b>Your Cart</b>\n\n"
        keyboard = []

        for item in cart_items:
            subtotal = item['price'] * item['quantity']
            text += f"• {item['quantity']}x <b>{item['name']}</b> - ₱{subtotal:.2f}\n"
            
            # Add/remove buttons for each item
            keyboard.append([
                {"text": "➖", "callback_data": f"cart:decrease:{item['id']}"},
                {"text": f"{item['quantity']}x {item['name']}", "callback_data": "noop"},
                {"text": "➕", "callback_data": f"cart:increase:{item['id']}"},
                {"text": "🗑️", "callback_data": f"cart:remove:{item['id']}"}
            ])

        text += f"\n<b>Total: ₱{total:.2f}</b>"

        keyboard.append([{"text": "🗑️ Clear Cart", "callback_data": "cart:clear"}])
        keyboard.append([{"text": "📋 Continue Shopping", "callback_data": "menu:back"}])
        keyboard.append([{"text": "✅ Checkout", "callback_data": "checkout:start"}])

        return await self.send_message(
            user_id,
            text,
            self._build_inline_keyboard(keyboard)
        )

    async def send_order_confirmation(
        self,
        user_id: str,
        order: Dict
    ) -> bool:
        """Send order confirmation."""
        text = f"""
✅ <b>Order Confirmed!</b>

📝 <b>Order #{order['order_number']}</b>

<b>Items:</b>
"""
        for item in order['items']:
            text += f"• {item['quantity']}x {item['name']} - ₱{item['subtotal']:.2f}\n"

        text += f"""
<b>Total:</b> ₱{order['total']:.2f}

📍 <b>Delivery Address:</b>
{order['delivery_address']}

📞 <b>Phone:</b> {order['phone']}

Your order is being prepared! We'll notify you when it's ready.

Use /status to check your order status.
"""
        return await self.send_message(user_id, text)

    async def send_order_status_update(
        self,
        user_id: str,
        order_number: str,
        status: str
    ) -> bool:
        """Notify user of order status change."""
        status_messages = {
            'confirmed': '✅ Your order has been confirmed!',
            'preparing': '👨‍🍳 Your order is being prepared!',
            'ready': '🎉 Your order is ready for pickup/delivery!',
            'completed': '✅ Your order has been completed. Thank you!',
            'cancelled': '❌ Your order has been cancelled.'
        }
        
        status_text = status_messages.get(status, f'Order status: {status}')
        text = f"""
📢 <b>Order Update</b>

Order #{order_number}

{status_text}
"""
        return await self.send_message(user_id, text)

    async def edit_message(
        self,
        user_id: str,
        message_id: int,
        text: str,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """Edit an existing message."""
        data = {
            "chat_id": user_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = reply_markup
        
        result = await self._make_request("editMessageText", data)
        return result.get("ok", False)

    async def answer_callback(
        self,
        callback_id: str,
        text: Optional[str] = None
    ) -> bool:
        """Answer a callback query."""
        data = {"callback_query_id": callback_id}
        if text:
            data["text"] = text
        
        result = await self._make_request("answerCallbackQuery", data)
        return result.get("ok", False)


# Singleton instance
telegram_service = TelegramService()
