from django.contrib import admin
from .models import Product, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'status', 'created_at', 'total_amount']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]
    search_fields = ['email', 'shipping_name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available']
    list_filter = ['category', 'available']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}