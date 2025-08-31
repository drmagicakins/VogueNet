from django.urls import path
from . import views

urlpatterns = [
    # Paystack
    path("paystack/verify/<str:reference>/", views.paystack_verify, name="paystack_verify"),
    path("paystack/webhook/", views.paystack_webhook, name="paystack_webhook"),

    # Flutterwave
    path("flutterwave/verify/", views.flutterwave_verify, name="flutterwave_verify"),
    path("flutterwave/webhook/", views.flutterwave_webhook, name="flutterwave_webhook"),
    path("orders/mine/", views.my_orders, name="my_orders"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
]

