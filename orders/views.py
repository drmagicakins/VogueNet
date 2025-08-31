import json, uuid, decimal
import requests
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import Order, OrderItem
from .serializers import InitiateOrderSerializer, OrderSerializer
from products.models import Product


class InitiateOrderView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        """
        Expected payload:
        {
          "provider": "paystack" | "flutterwave",
          "email": "customer@example.com",
          "items": [{"product_id": 1, "quantity": 2}, ...]
        }
        """
        ser = InitiateOrderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # Build order from items
        total = decimal.Decimal("0.00")
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=data["email"],
            provider=data["provider"],
            total_amount=0,  # temp
        )

        for item in data["items"]:
            product = get_object_or_404(Product, id=item["product_id"])
            qty = item["quantity"]
            price = decimal.Decimal(str(product.price))
            total += price * qty
            OrderItem.objects.create(
                order=order, product=product, name=product.name, price=price, quantity=qty
            )

        order.total_amount = total
        order.save()

        # Initialize with provider
        if order.provider == "paystack":
            reference = f"psk_{uuid.uuid4().hex[:15]}"
            headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
            payload = {
                "email": order.email,
                "amount": int(order.total_amount * 100),  # kobo
                "currency": order.currency,
                "reference": reference,
                "callback_url": f"{settings.SITE_URL}/checkout-success/?provider=paystack&reference={reference}",
            }
            r = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=payload, timeout=30)
            resp = r.json()
            if r.status_code != 200 or not resp.get("status"):
                return Response({"detail": "Paystack init failed", "provider_response": resp}, status=400)
            order.reference = reference
            order.meta = resp
            order.save()
            return Response({
                "authorization_url": resp["data"]["authorization_url"],
                "reference": reference,
                "order": OrderSerializer(order).data,
            })

        elif order.provider == "flutterwave":
            tx_ref = f"flw_{uuid.uuid4().hex[:15]}"
            headers = {"Authorization": f"Bearer {settings.FLW_SECRET_KEY}", "Content-Type": "application/json"}
            payload = {
                "tx_ref": tx_ref,
                "amount": float(order.total_amount),  # NGN
                "currency": order.currency,
                "redirect_url": f"{settings.SITE_URL}/checkout-success/?provider=flutterwave&tx_ref={tx_ref}",
                "customer": {"email": order.email},
            }
            r = requests.post("https://api.flutterwave.com/v3/payments", headers=headers, json=payload, timeout=30)
            resp = r.json()
            if r.status_code not in (200, 201) or resp.get("status") not in ("success", "pending"):
                return Response({"detail": "Flutterwave init failed", "provider_response": resp}, status=400)
            order.reference = tx_ref  # store tx_ref here
            order.meta = resp
            order.save()
            return Response({
                "payment_link": resp["data"]["link"],
                "tx_ref": tx_ref,
                "order": OrderSerializer(order).data,
            })

        return Response({"detail": "Unsupported provider"}, status=400)


class VerifyOrderView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        Query params:
          - provider=paystack&reference=xxxx
          - provider=flutterwave&tx_id=12345  (or tx_ref=...)
        """
        provider = request.query_params.get("provider")
        if provider == "paystack":
            reference = request.query_params.get("reference")
            order = get_object_or_404(Order, provider="paystack", reference=reference)
            headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
            r = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers, timeout=30)
            resp = r.json()
            order.meta = resp
            if r.status_code == 200 and resp.get("status") and resp["data"]["status"] == "success":
                order.status = "paid"
            else:
                order.status = "failed"
            order.save()
            return Response(OrderSerializer(order).data)

        elif provider == "flutterwave":
            # You can arrive with tx_id or tx_ref; support both:
            tx_id = request.query_params.get("tx_id")
            tx_ref = request.query_params.get("tx_ref")
            if tx_id:
                order = get_object_or_404(Order, provider="flutterwave", tx_id=tx_id)
                url = f"https://api.flutterwave.com/v3/transactions/{tx_id}/verify"
            else:
                order = get_object_or_404(Order, provider="flutterwave", reference=tx_ref)
                # Need to first find the real transaction_id by ref — if you are saving it in your callback/webhook, great.
                # For simplicity, we’ll verify by ref using the standard verify endpoint that accepts tx_ref:
                url = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}"

            headers = {"Authorization": f"Bearer {settings.FLW_SECRET_KEY}"}
            r = requests.get(url, headers=headers, timeout=30)
            resp = r.json()
            order.meta = resp
            ok = (resp.get("status") in ("success", "completed")) or (resp.get("data", {}).get("status") == "successful")
            if ok:
                order.status = "paid"
                if not order.tx_id:
                    # try to store id if present
                    order.tx_id = str(resp.get("data", {}).get("id") or resp.get("id") or "")
            else:
                order.status = "failed"
            order.save()
            return Response(OrderSerializer(order).data)

        return Response({"detail": "Invalid provider"}, status=400)