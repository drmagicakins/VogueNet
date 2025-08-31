from rest_framework import viewsets, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404

from .models import Product, Comment, Like, Category
from .serializers import ProductSerializer, CommentSerializer, LikeSerializer
from .pagination import ProductPagination
# from django_filters.rest_framework import DjangoFilterBackend


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created')
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Filtering, searching, ordering
    # filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['price', 'category']
    search_fields = ['name', 'description']
    ordering_fields = ['created', 'price']
    pagination_class = ProductPagination

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(product_id=self.kwargs['product_pk'])

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, product_id=self.kwargs['product_pk'])


class LikeViewSet(viewsets.ModelViewSet):
    serializer_class = LikeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Like.objects.filter(product_id=self.kwargs['product_pk'])

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, product_id=self.kwargs['product_pk'])


# Best Sales: return top 8 products by sales_count
class BestSalesView(APIView):
    def get(self, request):
        products = Product.objects.order_by("-sales_count")[:8]
        serializer = ProductSerializer(products, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# Customers also purchased: recommend 8 random products
class CustomersAlsoPurchasedView(APIView):
    def get(self, request):
        products = Product.objects.order_by("?")[:8]
        serializer = ProductSerializer(products, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# Category view: renders category page with related products
def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.all()  # assumes related_name="products" in Product model
    return render(request, "category.html", {"category": category, "products": products})
