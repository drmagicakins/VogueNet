from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "name_snapshot", "price_kobo", "quantity"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    class Meta:
        model = Order
        fields = ["id", "status", "total_kobo", "created", "items"]


# Order receipt serializer

class OrderItemSerializer(serializers.ModelSerializer):
    price_naira = serializers.SerializerMethodField()
    product_id = serializers.IntegerField(source="product.id", read_only=True)

    def get_price_naira(self, obj):
        return obj.price_kobo / 100.0

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "name_snapshot", "price_kobo", "price_naira", "quantity"]

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    total_naira = serializers.SerializerMethodField()

    def get_total_naira(self, obj):
        return obj.total_kobo / 100.0

    class Meta:
        model = Order
        fields = ["id", "status", "total_kobo", "total_naira", "created", "items"]

