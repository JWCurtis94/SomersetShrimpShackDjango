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
    list_editable = ['status']  # ✅ Allow inline editing of status

    # ✅ Explicitly define editable fields and protect system ones
    fields = [
        'email', 'status',
        'shipping_name', 'shipping_address', 'shipping_city',
        'shipping_state', 'shipping_zip', 'shipping_country',
        'total_amount', 'created_at'
    ]
    readonly_fields = ['total_amount', 'created_at']


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
            obj.full_clean()
            super().save_model(request, obj, form, change)
            if not change:
                messages.success(request, f'Product "{obj.name}" was created successfully.')
        except ValidationError as e:
            error_message = "Validation Error: "
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    error_message += f"{field}: {', '.join(errors)}; "
            else:
                error_message += str(e)
            messages.error(request, error_message)
            raise
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving product {obj.name}: {str(e)}", exc_info=True)
            messages.error(request, f"Error saving product: {str(e)}")
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
        try:
            obj.full_clean()
            super().save_model(request, obj, form, change)
            if not change:
                messages.success(request, f'Category "{obj.name}" was created successfully.')
        except ValidationError as e:
            error_message = "Validation Error: "
            if hasattr(e, 'message_dict'):
                for field, errors in e.message_dict.items():
                    error_message += f"{field}: {', '.join(errors)}; "
            else:
                error_message += str(e)
            messages.error(request, error_message)
            raise
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving category {obj.name}: {str(e)}", exc_info=True)
            messages.error(request, f"Error saving category: {str(e)}")
            raise

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Categories - Use the Order field to control display order (lower numbers appear first)'
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('order', 'name')

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'

    def has_image(self, obj):
        return bool(obj.image)
    has_image.short_description = 'Image'
    has_image.boolean = True
