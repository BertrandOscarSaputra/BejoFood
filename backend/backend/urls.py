"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('webhook/', include('bot.urls')),
    path('api/v1/', include('dashboard.urls')),
]
