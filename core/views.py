from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from payments.models import Order

def index(request):
    return render(request, "index.html")

def products_page(request):
    return render(request, "products.html")

def register_page(request):
    return render(request, "register.html")

def login_page(request):
    return render(request, "login.html")

@login_required
def profile_page(request):
    return render(request, "profile.html")

@login_required
def upload_product_page(request):
    return render(request, "upload_product.html")

@login_required
def profile_orders(request):
    orders = Order.objects.filter(user=request.user).select_related("payment").prefetch_related("items").order_by("-created")
    return render(request, "profile_orders.html", {"orders": orders})


@login_required
def edit_profile_page(request):
    return render(request, "edit_profile.html")


def cart_page(request):
    return render(request, "cart.html")

def checkout_page(request, product_id):
    return render(request, "checkout.html", {"product_id": product_id})

def product_detail(request, product_id):
    return render(request, "product_detail.html", {"product_id": product_id})

# Newly added features below
def product_detail_page(request, product_id):
    return render(request, "product_detail.html", {"product_id": product_id})

@login_required
def edit_product_page(request, product_id):
    return render(request, "edit_product.html", {"product_id": product_id})

@login_required
def delete_product_page(request, product_id):
    return render(request, "delete_product.html", {"product_id": product_id})


def checkout_success(request):
    return render(request, "checkout_success.html")

def cart_page(request):
    from django.conf import settings
    return render(request, "cart.html", {
        "PAYSTACK_PUBLIC_KEY": settings.PAYSTACK_PUBLIC_KEY,
        "FLUTTERWAVE_PUBLIC_KEY": settings.FLUTTERWAVE_PUBLIC_KEY,
    })






