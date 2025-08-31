from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product

class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

class InitiateOrderSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=["paystack", "flutterwave"])
    email = serializers.EmailField()
    items = OrderItemInputSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Cart is empty.")
        return items

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product", "name", "price", "quantity"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = ["id", "email", "provider", "status", "total_amount", "currency", "reference", "tx_id", "items", "created"]
