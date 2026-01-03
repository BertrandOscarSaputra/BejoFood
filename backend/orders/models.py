from django.db import models
from core.models import TimestampedModel
from menu.models import MenuItem


class TelegramUser(TimestampedModel):
    """
    Telegram user who interacts with the bot
    """
    telegram_id = models.BigIntegerField(unique=True, db_index=True)
    username = models.CharField(max_length=150, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Conversation state for multi-step flows
    conversation_state = models.CharField(max_length=50, blank=True)
    conversation_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        if self.username:
            return f"@{self.username}"
        return f"{self.first_name} ({self.telegram_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class Cart(TimestampedModel):
    """
    Shopping cart for a user (one cart per user)
    """
    user = models.OneToOneField(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='cart'
    )

    def __str__(self):
        return f"Cart for {self.user}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def clear(self):
        self.items.all().delete()


class CartItem(TimestampedModel):
    """
    Individual item in a cart
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['cart', 'menu_item']

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    @property
    def subtotal(self):
        return self.menu_item.price * self.quantity


class OrderStatus(models.TextChoices):
    """Order status choices"""
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    PREPARING = 'preparing', 'Preparing'
    READY = 'ready', 'Ready for Pickup/Delivery'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class Order(TimestampedModel):
    """
    Customer order
    """
    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True
    )
    delivery_address = models.TextField()
    phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # For tracking
    order_number = models.CharField(max_length=20, unique=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number} - {self.user}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: BF-YYYYMMDD-XXXX
            from django.utils import timezone
            import random
            date_str = timezone.now().strftime('%Y%m%d')
            random_str = ''.join(random.choices('0123456789', k=4))
            self.order_number = f"BF-{date_str}-{random_str}"
        super().save(*args, **kwargs)

    @property
    def status_display(self):
        return self.get_status_display()


class OrderItem(TimestampedModel):
    """
    Individual item in an order (snapshot of menu item at order time)
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT
    )
    name = models.CharField(max_length=200)  # Snapshot
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Snapshot

    def __str__(self):
        return f"{self.quantity}x {self.name}"

    @property
    def subtotal(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # Snapshot menu item details
        if not self.name:
            self.name = self.menu_item.name
        if not self.price:
            self.price = self.menu_item.price
        super().save(*args, **kwargs)
