import json
import requests
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
from .models import Payment, Order, OrderItem

from django.contrib.auth import get_user_model
from products.models import Product

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import OrderSerializer, OrderDetailSerializer

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# --- PAYSTACK VERIFY ---
def paystack_verify(request, reference):
    """Verify Paystack transaction by reference."""
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    r = requests.get(url, headers=headers, timeout=20)
    data = r.json()

    if data.get("status") and data["data"]["status"] == "success":
        amount_kobo = data["data"]["amount"]  # integer in kobo
        # upsert payment
        pay, _ = Payment.objects.get_or_create(
            reference=reference,
            defaults={
                "gateway": "paystack",
                "amount_kobo": amount_kobo,
                "status": "success",
                "metadata": data["data"],
            },
        )
        if pay.status != "success":
            pay.status = "success"
            pay.amount_kobo = amount_kobo
            pay.metadata = data["data"]
            pay.save()
        return JsonResponse({"ok": True, "message": "Payment verified", "amount_kobo": amount_kobo})
    return JsonResponse({"ok": False, "message": "Verification failed", "raw": data}, status=400)

@csrf_exempt
def paystack_webhook(request):
    """
    Optional: handle Paystack webhooks (set the URL in Paystack dashboard).
    You can validate the signature via HTTP_X_PAYSTACK_SIGNATURE if desired.
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponse(status=400)

    event = payload.get("event")
    data = payload.get("data", {})
    reference = data.get("reference")
    if event == "charge.success" and reference:
        pay, _ = Payment.objects.get_or_create(
            reference=reference,
            defaults={
                "gateway": "paystack",
                "amount_kobo": data.get("amount", 0),
                "status": "success",
                "metadata": data,
            },
        )
        if pay.status != "success":
            pay.status = "success"
            pay.amount_kobo = data.get("amount", 0)
            pay.metadata = data
            pay.save()
    return HttpResponse(status=200)

# --- FLUTTERWAVE VERIFY ---
def flutterwave_verify(request):
    """
    Verify Flutterwave payment via transaction_id (?transaction_id=xxx).
    Frontend should redirect here with the transaction_id provided by Flutterwave.
    """
    tx_id = request.GET.get("transaction_id")
    if not tx_id:
        return JsonResponse({"ok": False, "message": "Missing transaction_id"}, status=400)

    url = f"https://api.flutterwave.com/v3/transactions/{tx_id}/verify"
    headers = {"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"}
    r = requests.get(url, headers=headers, timeout=20)
    data = r.json()

    if data.get("status") == "success" and data.get("data", {}).get("status") == "successful":
        amount = data["data"]["amount"]  # Naira float
        amount_kobo = int(float(amount) * 100)

        reference = data["data"].get("tx_ref") or get_random_string(18)
        pay, _ = Payment.objects.get_or_create(
            reference=reference,
            defaults={
                "gateway": "flutterwave",
                "amount_kobo": amount_kobo,
                "status": "success",
                "metadata": data["data"],
            },
        )
        if pay.status != "success":
            pay.status = "success"
            pay.amount_kobo = amount_kobo
            pay.metadata = data["data"]
            pay.save()
        return JsonResponse({"ok": True, "message": "Payment verified", "amount_kobo": amount_kobo})
    return JsonResponse({"ok": False, "message": "Verification failed", "raw": data}, status=400)

@csrf_exempt
def flutterwave_webhook(request):
    """Optional: handle Flutterwave webhooks."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponse(status=400)

    data = payload.get("data", {})
    if data.get("status") == "successful":
        reference = data.get("tx_ref")
        amount = data.get("amount", 0)
        amount_kobo = int(float(amount) * 100)
        pay, _ = Payment.objects.get_or_create(
            reference=reference,
            defaults={
                "gateway": "flutterwave",
                "amount_kobo": amount_kobo,
                "status": "success",
                "metadata": data,
            },
        )
        if pay.status != "success":
            pay.status = "success"
            pay.amount_kobo = amount_kobo
            pay.metadata = data
            pay.save()
    return HttpResponse(status=200)

# NEW LINE
def _create_order_from_payment_and_metadata(payment_obj, meta, request):
    """
    meta is expected to contain a 'cart' list with objects like:
    {id, name, price, quantity, image, ...}
    price is in Naira (string or number) on the front-end -> convert to kobo here.
    """
    if hasattr(payment_obj, "order"):
        return payment_obj.order  # already created

    cart = []
    if isinstance(meta, dict):
        cart = meta.get("cart") or meta.get("custom_fields") or []
    if not isinstance(cart, list):
        cart = []

    total_kobo = 0
    for item in cart:
        price_naira = float(item.get("price", 0))
        qty = int(item.get("quantity", 1))
        total_kobo += int(round(price_naira * 100)) * qty

    # Fallback to amount from payment if meta is empty
    if total_kobo == 0:
        total_kobo = payment_obj.amount_kobo

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        payment=payment_obj,
        total_kobo=total_kobo,
        status="paid",
        shipping_name="",
        shipping_email="",
    )

    # Create items
    for item in cart:
        pid = item.get("id")
        qty = int(item.get("quantity", 1))
        price_kobo = int(round(float(item.get("price", 0)) * 100))
        product = Product.objects.filter(id=pid).first()
        name_snapshot = item.get("name") or (product.name if product else "Product")
        OrderItem.objects.create(
            order=order,
            product=product,
            name_snapshot=name_snapshot,
            price_kobo=price_kobo,
            quantity=qty,
        )

    return order

# --- PAYSTACK VERIFY ---
def paystack_verify(request, reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    r = requests.get(url, headers=headers, timeout=20)
    data = r.json()

    if data.get("status") and data["data"]["status"] == "success":
        amount_kobo = data["data"]["amount"]
        meta = data["data"].get("metadata", {})

        pay, _ = Payment.objects.get_or_create(
            reference=reference,
            defaults={
                "gateway": "paystack",
                "amount_kobo": amount_kobo,
                "status": "success",
                "metadata": data["data"],
            },
        )
        if pay.status != "success":
            pay.status = "success"
            pay.amount_kobo = amount_kobo
            pay.metadata = data["data"]
            pay.save()

        # Create the order (idempotent)
        order = _create_order_from_payment_and_metadata(pay, meta, request)
        _send_order_email(order)
        return JsonResponse({"ok": True, "message": "Payment verified"})
    return JsonResponse({"ok": False, "message": "Verification failed", "raw": data}, status=400)

# --- FLUTTERWAVE VERIFY ---
def flutterwave_verify(request):
    tx_id = request.GET.get("transaction_id")
    if not tx_id:
        return JsonResponse({"ok": False, "message": "Missing transaction_id"}, status=400)

    url = f"https://api.flutterwave.com/v3/transactions/{tx_id}/verify"
    headers = {"Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}"}
    r = requests.get(url, headers=headers, timeout=20)
    data = r.json()

    if data.get("status") == "success" and data.get("data", {}).get("status") == "successful":
        amount = data["data"]["amount"]
        amount_kobo = int(float(amount) * 100)
        reference = data["data"].get("tx_ref") or get_random_string(18)
        meta = data["data"].get("meta", {})  # Flutterwave returns 'meta'

        pay, _ = Payment.objects.get_or_create(
            reference=reference,
            defaults={
                "gateway": "flutterwave",
                "amount_kobo": amount_kobo,
                "status": "success",
                "metadata": data["data"],
            },
        )
        if pay.status != "success":
            pay.status = "success"
            pay.amount_kobo = amount_kobo
            pay.metadata = data["data"]
            pay.save()

        _create_order_from_payment_and_metadata(pay, meta, request)
        order = _create_order_from_payment_and_metadata(pay, meta, request)
        _send_order_email(order)
        return JsonResponse({"ok": True, "message": "Payment verified"})
    return JsonResponse({"ok": False, "message": "Verification failed", "raw": data}, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_orders(request):
    qs = Order.objects.filter(user=request.user).order_by("-created")
    return Response(OrderSerializer(qs, many=True).data)

# Email user on order success
def _send_order_email(order):
    """Send a simple HTML + text receipt to the buyer (if we have an email)."""
    # Try to pick an email in priority order
    to_email = (order.shipping_email or
                (order.user.email if order.user and order.user.email else None))
    if not to_email:
        return

    ctx = {"order": order}
    html = render_to_string("emails/order_receipt.html", ctx)
    text = strip_tags(html)
    subj = f"Your VogueNet order #{order.id} – paid"

    send_mail(
        subject=subj,
        message=text,
        from_email=None,   # uses DEFAULT_FROM_EMAIL
        recipient_list=[to_email],
        html_message=html,
        fail_silently=True,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    order = Order.objects.filter(id=pk, user=request.user).prefetch_related("items").first()
    if not order:
        return Response({"detail": "Not found."}, status=404)
    return Response(OrderDetailSerializer(order).data)

