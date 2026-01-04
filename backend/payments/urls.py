from django.urls import path
from . import views

urlpatterns = [
    path('midtrans/', views.midtrans_webhook, name='midtrans_webhook'),
]
