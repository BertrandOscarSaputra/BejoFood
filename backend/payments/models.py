from django.db import models
from core.models import TimestampedModel
from orders.models import Order


class PaymentStatus(models.TextChoices):
    """Payment status choices based on Midtrans statuses"""
    PENDING = 'pending', 'Pending'
    SETTLEMENT = 'settlement', 'Paid'
    EXPIRE = 'expire', 'Expired'
    DENY = 'deny', 'Denied'
    CANCEL = 'cancel', 'Cancelled'


class Payment(TimestampedModel):
    """
    QRIS Payment record linked to an Order.
    Tracks Midtrans transaction details and status.
    """
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    
    # Midtrans transaction details
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_type = models.CharField(max_length=50, default='qris')
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    
    # QR Code
    qr_url = models.URLField(blank=True)
    qr_string = models.TextField(blank=True)  # Raw QR data
    
    # Amount
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Timing
    expires_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Raw response storage
    midtrans_response = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.status}"

    @property
    def is_paid(self):
        return self.status == PaymentStatus.SETTLEMENT

    @property
    def is_expired(self):
        return self.status == PaymentStatus.EXPIRE
