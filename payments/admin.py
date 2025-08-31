from django.contrib import admin
from .models import Payment, Order, OrderItem

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "gateway", "status", "amount_kobo", "created")
    search_fields = ("reference", "gateway", "status")
    list_filter = ("gateway", "status", "created")

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "payment", "user", "status", "total_kobo", "created")
    search_fields = ("payment__reference", "user__username")
    list_filter = ("status", "created")
    inlines = [OrderItemInline]
