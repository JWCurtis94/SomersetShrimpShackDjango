from django.contrib import admin
from .models import Product, Order, OrderItem, Category

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

# Custom admin view for Categories
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'has_image', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_per_page = 20
    fields = ['name', 'slug', 'description', 'image']
    
    def product_count(self, obj):
        """Display the number of products in this category"""
        return obj.products.count()
    product_count.short_description = 'Products'
    
    def has_image(self, obj):
        """Display whether category has an image"""
        return bool(obj.image)
    has_image.short_description = 'Image'
    has_image.boolean = True
