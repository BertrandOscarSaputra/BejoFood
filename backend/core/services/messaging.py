"""
Abstract messaging service layer.
Allows swapping between Telegram, WhatsApp, etc. without changing business logic.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class MessagingService(ABC):
    """
    Abstract base class for messaging platforms.
    Implement this for each platform (Telegram, WhatsApp, etc.)
    """

    @abstractmethod
    async def send_message(
        self,
        user_id: str,
        text: str,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """Send a text message to a user."""
        pass

    @abstractmethod
    async def send_menu(
        self,
        user_id: str,
        categories: List[Dict]
    ) -> bool:
        """Send menu categories as interactive buttons."""
        pass

    @abstractmethod
    async def send_items(
        self,
        user_id: str,
        category_name: str,
        items: List[Dict]
    ) -> bool:
        """Send menu items for a specific category."""
        pass

    @abstractmethod
    async def send_cart(
        self,
        user_id: str,
        cart_items: List[Dict],
        total: float
    ) -> bool:
        """Send cart contents to user."""
        pass

    @abstractmethod
    async def send_order_confirmation(
        self,
        user_id: str,
        order: Dict
    ) -> bool:
        """Send order confirmation with details."""
        pass

    @abstractmethod
    async def send_order_status_update(
        self,
        user_id: str,
        order_number: str,
        status: str
    ) -> bool:
        """Notify user of order status change."""
        pass

    @abstractmethod
    async def edit_message(
        self,
        user_id: str,
        message_id: int,
        text: str,
        reply_markup: Optional[Any] = None
    ) -> bool:
        """Edit an existing message."""
        pass

    @abstractmethod
    async def answer_callback(
        self,
        callback_id: str,
        text: Optional[str] = None
    ) -> bool:
        """Answer a callback query (button click)."""
        pass
