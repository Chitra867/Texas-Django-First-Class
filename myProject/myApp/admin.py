from django.contrib import admin
from .models import Category, Product, Cart, Customer

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'description', 'stock', 'featured']
    list_filter = ['category', 'featured']
    search_fields = ['name', 'description']
    list_editable = ['price', 'description', 'stock', 'featured']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'added_at']
    list_filter = ['added_at']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'address', 'joined_at']
    search_fields = ['user__username', 'phone']

 