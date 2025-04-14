from django.contrib import admin
from .models import Product, Order, OrderItem

# Inline display of OrderItem within Order admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# Custom admin view for Orders
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'status', 'created_at', 'total_amount']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]
    search_fields = ['email', 'shipping_name']

# Custom admin view for Products
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available']
    list_filter = ['category', 'available']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
