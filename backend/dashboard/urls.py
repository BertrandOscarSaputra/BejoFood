"""
Dashboard API URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'menu-items', views.MenuItemViewSet, basename='menu-item')

app_name = 'dashboard'

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', views.DashboardStatsView.as_view(), name='stats'),
]
