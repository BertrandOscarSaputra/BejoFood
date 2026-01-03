from django.contrib import admin
from .models import TelegramUser, Cart, CartItem, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['subtotal']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'username', 'first_name', 'last_name', 'phone', 'created_at']
    search_fields = ['telegram_id', 'username', 'first_name', 'last_name', 'phone']
    readonly_fields = ['telegram_id', 'created_at', 'updated_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'item_count', 'total', 'updated_at']
    inlines = [CartItemInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total', 'phone', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'user__first_name', 'user__phone', 'phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    actions = ['mark_as_preparing', 'mark_as_ready', 'mark_as_completed']

    def mark_as_preparing(self, request, queryset):
        queryset.update(status='preparing')
    mark_as_preparing.short_description = "Mark selected orders as Preparing"

    def mark_as_ready(self, request, queryset):
        queryset.update(status='ready')
    mark_as_ready.short_description = "Mark selected orders as Ready"

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = "Mark selected orders as Completed"
