from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order', 'status', 'gross_amount', 'created_at', 'paid_at']
    list_filter = ['status', 'payment_type', 'created_at']
    search_fields = ['transaction_id', 'order__order_number']
    readonly_fields = ['transaction_id', 'qr_url', 'qr_string', 'midtrans_response', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order', 'gross_amount')
        }),
        ('Transaction', {
            'fields': ('transaction_id', 'payment_type', 'status')
        }),
        ('QR Code', {
            'fields': ('qr_url', 'qr_string')
        }),
        ('Timestamps', {
            'fields': ('expires_at', 'paid_at', 'created_at', 'updated_at')
        }),
        ('Raw Response', {
            'fields': ('midtrans_response',),
            'classes': ('collapse',)
        }),
    )
