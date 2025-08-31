from django.urls import path
from . import views
from django.views.generic import TemplateView
from .views import index, products_page, register_page, login_page, profile_page, upload_product_page, edit_profile_page, cart_page, product_detail_page, edit_product_page, delete_product_page, checkout_page, product_detail


urlpatterns = [
    path('', index, name='home'),
    path('products/', products_page, name='products'),
    path('men/', products_page, name='men'), # added this line
    path('register/', register_page, name='register'),  # fix here
    path('login/', login_page, name='login'),            # fix here
    path('profile/', profile_page, name='profile'),
    path('upload/', upload_product_page, name='upload_product'),
    path('profile/edit/', edit_profile_page, name='edit_profile'),
    path('cart/', cart_page, name='cart'),
    path("checkout/", checkout_page, name="checkout"),
    path("checkout-success/", TemplateView.as_view(template_name="checkout_success.html"), name="checkout_success"),
    path("profile/orders/", views.profile_orders, name="profile_orders"),

    path('products/<int:product_id>/', product_detail_page, name='product_detail_page'),  # fix here
    path("products/<int:pk>/", product_detail, name="product_detail"),
    path('products/<int:product_id>/edit/', edit_product_page, name='edit_product'),
    path('products/<int:product_id>/delete/', delete_product_page, name='delete_product'),

    path('product_detail/1', product_detail_page, name='product_detail')

]