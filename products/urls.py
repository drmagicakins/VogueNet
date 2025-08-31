from django.urls import path, include
from rest_framework_nested import routers
from .views import (
    ProductViewSet,
    CommentViewSet,
    LikeViewSet,
    BestSalesView,
    CustomersAlsoPurchasedView,
    category_view,
)

# Base router for products
router = routers.SimpleRouter()
router.register(r'products', ProductViewSet, basename="products")

# Nested routers for comments & likes
products_nested_router = routers.NestedSimpleRouter(router, r'products', lookup='product')
products_nested_router.register(r'comments', CommentViewSet, basename='product-comments')
products_nested_router.register(r'likes', LikeViewSet, basename='product-likes')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(products_nested_router.urls)),

    # Extra API endpoints
    path("api/products/best-sales/", BestSalesView.as_view(), name="best-sales"),
    path("api/products/customers-also-purchased/", CustomersAlsoPurchasedView.as_view(), name="customers-also-purchased"),

    # Category view
    path("category/<slug:slug>/", category_view, name="category"),
]
