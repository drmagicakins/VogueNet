from django.contrib import admin
from .models import Category, Product, Comment, Like

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}  # auto-generate slug

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'sales_count', 'created')
    list_filter = ('category', 'created')
    search_fields = ('name', 'description')
    prepopulated_fields = {"slug": ("name",)}  # auto-generate slug

admin.site.register(Comment)
admin.site.register(Like)
