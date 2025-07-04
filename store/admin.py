from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
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
    list_editable = ['stock', 'available']
    
    def save_model(self, request, obj, form, change):
        """Custom save method to handle potential errors"""
        try:
            # Call the model's clean method first
            obj.full_clean()
            super().save_model(request, obj, form, change)
            if not change:  # Only show message for new products
                messages.success(request, f'Product "{obj.name}" was created successfully.')
        except ValidationError as e:
            # Handle validation errors gracefully
            error_message = "Validation Error: "
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    error_message += f"{field}: {', '.join(errors)}; "
            else:
                error_message += str(e)
            messages.error(request, error_message)
            raise
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving product {obj.name}: {str(e)}", exc_info=True)
            messages.error(request, f"Error saving product: {str(e)}")
            # Re-raise the exception so the user sees the error
            raise

# Custom admin view for Categories
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'slug', 'product_count', 'has_image', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    list_per_page = 20
    list_editable = ['order']
    ordering = ['order', 'name']
    fields = ['name', 'slug', 'description', 'image', 'order']
    
    def save_model(self, request, obj, form, change):
        """Custom save method to handle potential errors"""
        try:
            # Call the model's clean method first
            obj.full_clean()
            super().save_model(request, obj, form, change)
            if not change:  # Only show message for new categories
                messages.success(request, f'Category "{obj.name}" was created successfully.')
        except ValidationError as e:
            # Handle validation errors gracefully
            error_message = "Validation Error: "
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    error_message += f"{field}: {', '.join(errors)}; "
            else:
                error_message += str(e)
            messages.error(request, error_message)
            raise
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving category {obj.name}: {str(e)}", exc_info=True)
            messages.error(request, f"Error saving category: {str(e)}")
            # Re-raise the exception so the user sees the error
            raise
    
    # Add some helpful text at the top of the admin
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Categories - Use the Order field to control display order (lower numbers appear first)'
        return super().changelist_view(request, extra_context=extra_context)
    
    def get_queryset(self, request):
        """Ensure categories are ordered properly in admin"""
        return super().get_queryset(request).order_by('order', 'name')
    
    def product_count(self, obj):
        """Display the number of products in this category"""
        return obj.products.count()
    product_count.short_description = 'Products'
    
    def has_image(self, obj):
        """Display whether category has an image"""
        return bool(obj.image)
    has_image.short_description = 'Image'
    has_image.boolean = True
