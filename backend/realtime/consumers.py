"""
WebSocket consumers for real-time order updates.
"""
import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


class OrderConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for real-time order updates.
    Dashboard clients connect here to receive instant notifications.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        # Add to orders group
        await self.channel_layer.group_add('orders', self.channel_name)
        await self.accept()
        
        logger.info(f"Dashboard client connected: {self.channel_name}")

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard('orders', self.channel_name)
        logger.info(f"Dashboard client disconnected: {self.channel_name}")

    async def receive_json(self, content):
        """Handle incoming messages from client."""
        action = content.get('action')
        
        if action == 'ping':
            await self.send_json({'action': 'pong'})
        elif action == 'subscribe':
            # Could implement room-based subscriptions here
            await self.send_json({'action': 'subscribed', 'channel': 'orders'})

    async def order_update(self, event):
        """
        Handle order update events from the channel layer.
        Called when a new order is placed or status changes.
        """
        data = event.get('data', {})
        await self.send_json({
            'type': 'order_update',
            'data': data
        })
