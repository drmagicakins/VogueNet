from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model() 


class Payment(models.Model):
    GATEWAYS = (("paystack", "Paystack"), ("flutterwave", "Flutterwave"))
    STATUSES = (("pending","Pending"),("success","Success"),("failed","Failed"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    reference = models.CharField(max_length=100, unique=True)
    amount_kobo = models.PositiveIntegerField()  # Paystack uses kobo
    gateway = models.CharField(max_length=20, choices=GATEWAYS)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    metadata = models.JSONField(default=dict, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference} - {self.gateway} - {self.status}"

class Order(models.Model):
    STATUSES = (("paid", "Paid"), ("refunded", "Refunded"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments_module_orders")
    payment = models.OneToOneField("payments.Payment", on_delete=models.CASCADE, related_name="order")
    total_kobo = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUSES, default="paid")
    shipping_name = models.CharField(max_length=200, blank=True, default="")
    shipping_email = models.EmailField(blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} / {self.payment.reference} / {self.status}"

    @property
    def total_naira(self):
        return self.total_kobo / 100.0

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="payments_module_order_items")
    name_snapshot = models.CharField(max_length=255)  # denormalized name at purchase time
    price_kobo = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    def line_total_kobo(self):
        return self.price_kobo * self.quantity

    def __str__(self):
        return f"{self.name_snapshot} x{self.quantity}"

