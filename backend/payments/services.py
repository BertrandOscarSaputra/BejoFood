"""
Midtrans QRIS Payment Service.
Handles QRIS generation, webhook verification, and payment processing.
"""
import midtransclient
import hashlib
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class MidtransService:
    """
    Service for interacting with Midtrans QRIS API.
    """
    
    def __init__(self):
        self.is_production = getattr(settings, 'MIDTRANS_IS_PRODUCTION', False)
        self.server_key = settings.MIDTRANS_SERVER_KEY
        self.client_key = settings.MIDTRANS_CLIENT_KEY
        
        # Initialize Midtrans Core API client
        self.core_api = midtransclient.CoreApi(
            is_production=self.is_production,
            server_key=self.server_key,
            client_key=self.client_key
        )
    
    def create_qris_payment(self, order):
        """
        Create a QRIS payment for an order.
        Returns dict with QR URL, transaction_id, and expiry time.
        """
        from .models import Payment
        
        # Build transaction details
        order_id = f"{order.order_number}-{int(timezone.now().timestamp())}"
        gross_amount = int(order.total)  # Midtrans requires integer
        
        # Build item details
        items = []
        for item in order.items.all():
            items.append({
                'id': str(item.menu_item_id),
                'name': item.name[:50],  # Max 50 chars
                'price': int(item.price),
                'quantity': item.quantity
            })
        
        # Customer details
        customer = {
            'first_name': order.user.first_name,
            'last_name': order.user.last_name or '',
            'phone': order.phone
        }
        
        # QRIS specific parameters
        param = {
            'payment_type': 'qris',
            'transaction_details': {
                'order_id': order_id,
                'gross_amount': gross_amount
            },
            'item_details': items,
            'customer_details': customer,
            'qris': {
                'acquirer': 'gopay'  # Can be gopay or airpay (shopeepay)
            }
        }
        
        try:
            # Call Midtrans Charge API
            response = self.core_api.charge(param)
            logger.info(f"Midtrans QRIS response: {response}")
            
            if response.get('status_code') == '201':
                # Parse expiry time (15 minutes from now)
                expires_at = timezone.now() + timedelta(minutes=15)
                
                # Get QR code URL from actions
                qr_url = ''
                qr_string = ''
                actions = response.get('actions', [])
                for action in actions:
                    if action.get('name') == 'generate-qr-code':
                        qr_url = action.get('url', '')
                    elif action.get('name') == 'deeplink-redirect':
                        pass  # For mobile deep links
                
                # Also check direct qr_string field
                qr_string = response.get('qr_string', '')
                
                # Create Payment record
                payment = Payment.objects.create(
                    order=order,
                    transaction_id=response.get('transaction_id'),
                    payment_type='qris',
                    status='pending',
                    qr_url=qr_url,
                    qr_string=qr_string,
                    gross_amount=gross_amount,
                    expires_at=expires_at,
                    midtrans_response=response
                )
                
                return {
                    'success': True,
                    'payment': payment,
                    'qr_url': qr_url,
                    'qr_string': qr_string,
                    'transaction_id': response.get('transaction_id'),
                    'expires_at': expires_at
                }
            else:
                logger.error(f"Midtrans error: {response}")
                return {
                    'success': False,
                    'error': response.get('status_message', 'Payment creation failed')
                }
                
        except Exception as e:
            logger.exception(f"Midtrans API error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_signature(self, order_id, status_code, gross_amount, signature_key):
        """
        Verify Midtrans webhook signature.
        """
        # Signature = SHA512(order_id + status_code + gross_amount + server_key)
        raw_string = f"{order_id}{status_code}{gross_amount}{self.server_key}"
        calculated_signature = hashlib.sha512(raw_string.encode()).hexdigest()
        
        return calculated_signature == signature_key
    
    def handle_notification(self, notification_data):
        """
        Process payment notification from Midtrans webhook.
        Returns tuple of (success, message).
        """
        from .models import Payment
        from orders.models import OrderStatus
        
        order_id = notification_data.get('order_id')
        transaction_id = notification_data.get('transaction_id')
        transaction_status = notification_data.get('transaction_status')
        signature_key = notification_data.get('signature_key')
        status_code = notification_data.get('status_code')
        gross_amount = notification_data.get('gross_amount')
        
        # Verify signature
        if not self.verify_signature(order_id, status_code, gross_amount, signature_key):
            logger.warning(f"Invalid signature for transaction {transaction_id}")
            return False, "Invalid signature"
        
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for transaction {transaction_id}")
            return False, "Payment not found"
        
        # Update payment status
        old_status = payment.status
        
        if transaction_status == 'settlement':
            payment.status = 'settlement'
            payment.paid_at = timezone.now()
            payment.order.status = OrderStatus.CONFIRMED
            payment.order.save()
            
        elif transaction_status == 'pending':
            payment.status = 'pending'
            
        elif transaction_status in ['deny', 'cancel']:
            payment.status = transaction_status
            payment.order.status = OrderStatus.CANCELLED
            payment.order.save()
            
        elif transaction_status == 'expire':
            payment.status = 'expire'
            payment.order.status = OrderStatus.CANCELLED
            payment.order.save()
        
        payment.midtrans_response = notification_data
        payment.save()
        
        logger.info(f"Payment {transaction_id} status updated: {old_status} -> {payment.status}")
        
        return True, f"Status updated to {payment.status}"


# Singleton instance
midtrans_service = MidtransService()
