"""
REST API serializers for dashboard.
"""
from rest_framework import serializers
from orders.models import Order, OrderItem, TelegramUser, OrderStatus
from menu.models import Category, MenuItem


class TelegramUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramUser
        fields = ['id', 'telegram_id', 'username', 'first_name', 'last_name', 'phone']


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'price']


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'name', 'quantity', 'price', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    user = TelegramUserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'status_display',
            'delivery_address', 'phone', 'notes', 'total',
            'items', 'created_at', 'updated_at'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list view."""
    user = TelegramUserSerializer(read_only=True)
    item_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(read_only=True)
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'status', 'status_display',
            'total', 'item_count', 'payment_status', 'created_at'
        ]

    def get_item_count(self, obj):
        return obj.items.count()

    def get_payment_status(self, obj):
        # Get the payment for this order (OneToOne relationship)
        try:
            return obj.payment.status if hasattr(obj, 'payment') else None
        except:
            return None


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status."""
    status = serializers.ChoiceField(choices=OrderStatus.choices)


class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'emoji', 'description', 'is_active', 'order', 'item_count']

    def get_item_count(self, obj):
        return obj.items.count()


class MenuItemFullSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'category_name', 'name', 'description',
            'price', 'image_url', 'is_available'
        ]
