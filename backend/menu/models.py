from django.db import models
from core.models import TimestampedModel


class Category(TimestampedModel):
    """
    Food category (e.g., Appetizers, Main Course, Beverages)
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    emoji = models.CharField(max_length=10, blank=True, help_text="Emoji for Telegram display")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order in menu")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.emoji} {self.name}" if self.emoji else self.name


class MenuItem(TimestampedModel):
    """
    Individual menu item within a category
    """
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_url = models.URLField(blank=True, help_text="URL to item image")
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['category__order', 'name']

    def __str__(self):
        return f"{self.name} - ₱{self.price}"
