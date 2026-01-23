"""
REST API views for dashboard.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from orders.models import Order, OrderStatus, TelegramUser
from menu.models import Category, MenuItem

from .serializers import (
    OrderSerializer, OrderListSerializer, OrderStatusUpdateSerializer,
    CategorySerializer, MenuItemFullSerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    """
    queryset = Order.objects.select_related('user').prefetch_related('items__menu_item').all()
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update order status and notify customer."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            new_status = serializer.validated_data['status']
            old_status = order.status
            
            order.status = new_status
            order.save()
            
            # Notify customer via Telegram
            self._notify_customer(order, new_status)
            
            # Notify dashboard via WebSocket
            self._notify_dashboard(order, old_status, new_status)
            
            return Response({
                'success': True,
                'order_number': order.order_number,
                'old_status': old_status,
                'new_status': new_status
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _notify_customer(self, order, new_status):
        """Send status update to customer via Telegram."""
        from asgiref.sync import async_to_sync
        from core.services.telegram import telegram_service
        
        try:
            async_to_sync(telegram_service.send_order_status_update)(
                str(order.user.telegram_id),
                order.order_number,
                new_status
            )
        except Exception as e:
            # Log but don't fail the request
            import logging
            logging.error(f"Failed to notify customer: {e}")

    def _notify_dashboard(self, order, old_status, new_status):
        """Send update to dashboard via WebSocket."""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            try:
                async_to_sync(channel_layer.group_send)(
                    'orders',
                    {
                        'type': 'order_update',
                        'data': {
                            'action': 'status_changed',
                            'order_id': order.id,
                            'order_number': order.order_number,
                            'old_status': old_status,
                            'new_status': new_status
                        }
                    }
                )
            except Exception as e:
                import logging
                logging.error(f"Failed to notify dashboard: {e}")


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing menu categories."""
    queryset = Category.objects.annotate(item_count=Count('items')).all()
    serializer_class = CategorySerializer


class MenuItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing menu items."""
    queryset = MenuItem.objects.select_related('category').all()
    serializer_class = MenuItemFullSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by availability
        available = self.request.query_params.get('available')
        if available is not None:
            queryset = queryset.filter(is_available=available.lower() == 'true')
        
        return queryset


class DashboardStatsView(APIView):
    """Dashboard statistics endpoint."""

    def get(self, request):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # Valid statuses for revenue
        valid_statuses = [
            OrderStatus.CONFIRMED,
            OrderStatus.PREPARING,
            OrderStatus.READY,
            OrderStatus.COMPLETED
        ]

        # Today's stats
        today_orders = Order.objects.filter(
            created_at__date=today,
            status__in=valid_statuses
        )
        today_revenue = today_orders.aggregate(total=Sum('total'))['total'] or 0
        
        # Pending orders count
        pending_orders = Order.objects.filter(
            status__in=[OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING]
        ).count()

        # Weekly stats
        weekly_orders = Order.objects.filter(
            created_at__date__gte=week_ago,
            status__in=valid_statuses
        )
        weekly_revenue = weekly_orders.aggregate(total=Sum('total'))['total'] or 0

        # Order status breakdown
        status_counts = dict(
            Order.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )

        # Total customers
        total_customers = TelegramUser.objects.count()

        return Response({
            'today': {
                'orders': today_orders.count(),
                'revenue': float(today_revenue)
            },
            'weekly': {
                'orders': weekly_orders.count(),
                'revenue': float(weekly_revenue)
            },
            'pending_orders': pending_orders,
            'total_customers': total_customers,
            'status_breakdown': status_counts
        })
