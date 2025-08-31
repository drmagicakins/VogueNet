from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class Order(models.Model):
    PROVIDERS = [
        ("paystack", "Paystack"),
        ("flutterwave", "Flutterwave"),
    ]
    STATUSES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders_module_orders"  # 👈 unique name to avoid clash
    )
    email = models.EmailField()
    provider = models.CharField(max_length=20, choices=PROVIDERS)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=5, default="NGN")

    # Provider identifiers
    reference = models.CharField(max_length=100, blank=True, null=True)    # Paystack
    tx_id = models.CharField(max_length=100, blank=True, null=True)        # Flutterwave

    meta = models.JSONField(default=dict, blank=True)  # store raw provider response safely
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.provider.upper()} {self.reference or self.tx_id} - {self.status}"
    
    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="orders_module_order_items"  # 👈 unique name to avoid clash
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def line_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.name} x{self.quantity}"
    
    def __str__(self):
        return f"{self.quantity} × {self.product.name}"
    


@receiver(post_save, sender=OrderItem)
def update_sales_count(sender, instance, created, **kwargs):
    if created:  # only on first creation
        product = instance.product
        product.sales_count += instance.quantity
        product.save()

        


