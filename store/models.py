from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, RegexValidator
from django.utils.text import slugify
from django.db.models import Sum, F
from django.urls import reverse
from decimal import Decimal
import uuid

# Function to generate unique slug
def generate_unique_slug(instance, max_length=255):
    """Generate a unique slug for the product name"""
    base_slug = slugify(instance.name)
    
    # Truncate base slug if too long, leaving room for counter
    if len(base_slug) > max_length - 10:
        base_slug = base_slug[:max_length - 10]
    
    slug = base_slug
    counter = 1
    
    # Get the model class
    model_class = instance.__class__
    
    # Handle updating existing products correctly
    while True:
        if instance.pk:
            query = model_class.objects.filter(slug=slug).exclude(pk=instance.pk)
        else:
            query = model_class.objects.filter(slug=slug)
        
        if not query.exists():
            break
            
        slug = f"{base_slug}-{counter}"
        counter += 1
        
        # Safety check to prevent infinite loops
        if counter > 9999:
            import uuid
            slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            break
    
    return slug

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True, max_length=100, blank=True)
    image = models.ImageField(
        upload_to='categories/', 
        blank=True, 
        null=True,
        help_text="Category image for display on the website"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order for displaying categories (lower numbers appear first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        """Return the URL for this category"""
        return reverse('store:category_detail', args=[self.slug])
    
    def get_next_order(self):
        """Get the next available order number"""
        last_category = Category.objects.exclude(pk=self.pk).order_by('order').last()
        if last_category:
            return last_category.order + 10
        return 10
    
    def clean(self):
        """Validate the category model"""
        from django.core.exceptions import ValidationError
        
        # Validate image file if provided
        if self.image:
            # Check file size (max 5MB)
            if hasattr(self.image, 'size') and self.image.size > 5 * 1024 * 1024:
                raise ValidationError({'image': 'Image file too large. Maximum size is 5MB.'})
            
            # Check file extension
            if hasattr(self.image, 'name'):
                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                file_extension = self.image.name.lower().split('.')[-1]
                if f'.{file_extension}' not in valid_extensions:
                    raise ValidationError({'image': f'Invalid image format. Allowed formats: {", ".join(valid_extensions)}'})
        
        # Validate name
        if not self.name or not self.name.strip():
            raise ValidationError({'name': 'Category name is required.'})
        
        # Ensure name is unique (case-insensitive)
        if self.pk:
            existing = Category.objects.filter(name__iexact=self.name.strip()).exclude(pk=self.pk).first()
        else:
            existing = Category.objects.filter(name__iexact=self.name.strip()).first()
        
        if existing:
            raise ValidationError({'name': 'A category with this name already exists.'})
    
    def save(self, *args, **kwargs):
        # Strip whitespace from name
        self.name = self.name.strip() if self.name else ''
        
        # Auto-assign order if not set
        if self.order == 0:
            self.order = self.get_next_order()
        
        # Generate slug before validation
        if not self.slug:
            self.slug = generate_unique_slug(self)
        
        # Always run clean() before saving
        self.full_clean()
        
        super().save(*args, **kwargs)
    
# Define constant choices at module level
SIZE_CHOICES = [
    ('small', 'Small'),
    ('medium', 'Medium'),
    ('large', 'Large'),
]

class ProductManager(models.Manager):
    """Custom manager for Product model with common queries"""
    
    def available(self):
        """Return only available products"""
        return self.filter(available=True)
    
    def in_stock(self):
        """Return products that are available and in stock"""
        return self.filter(available=True, stock__gt=0)
    
    def featured(self):
        """Return featured products that are available"""
        return self.filter(featured=True, available=True)
    
    def low_stock(self, threshold=5):
        """Return products with low stock"""
        return self.filter(available=True, stock__lte=threshold, stock__gt=0)
    
    def by_category(self, category):
        """Return products in a specific category"""
        return self.filter(category=category, available=True)

class Product(models.Model):
    """
    Model representing inventory products available for sale
    """
    # FIX: Use db_column parameter to match existing column name in database
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products',
        db_column='category_id'  # Explicitly set the database column name
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)
    description = models.TextField(blank=True)
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO meta description")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True, null=True)
    image = models.ImageField(
        upload_to='products/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    available = models.BooleanField(default=True, db_index=True)
    featured = models.BooleanField(default=False, help_text="Feature this product on the homepage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom manager
    objects = ProductManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['available', 'price']),  # For price filtering on available products
            models.Index(fields=['available', 'stock']),  # For stock filtering on available products  
            models.Index(fields=['available', 'created_at']),  # For newest sorting on available products
            models.Index(fields=['category', 'available']),  # For category filtering on available products
            models.Index(fields=['price', 'available'], name='prod_price_avail_idx'),
            models.Index(fields=['featured', 'available'], name='prod_feat_avail_idx'),
            models.Index(fields=['size', 'category'], name='prod_size_cat_idx'),
        ]
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = generate_unique_slug(self)

        # FIX: Re-enable automatic availability setting based on stock
        # Only set available=False when stock becomes 0, never automatically set to True
        if self.stock <= 0:
            self.available = False

        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate product data"""
        from django.core.exceptions import ValidationError
        
        # Ensure price is reasonable
        if self.price and self.price > Decimal('9999.99'):
            raise ValidationError({'price': 'Price cannot exceed £9,999.99'})
        
        # Ensure stock is reasonable
        if self.stock and self.stock > 99999:
            raise ValidationError({'stock': 'Stock cannot exceed 99,999 items'})
        
        # Validate name length
        if self.name and len(self.name.strip()) < 2:
            raise ValidationError({'name': 'Product name must be at least 2 characters long'})
        
        super().clean()

    def __str__(self):
        if self.size:
            return f"{self.name} - {self.get_size_display()}"
        return self.name

    def get_absolute_url(self):
        """Return the URL for this product"""
        return reverse('store:product_detail', args=[self.slug])

    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock > 0 and self.available

    @property
    def display_price(self):
        """Return price formatted for display with £ symbol"""
        return f"£{self.price}"

    @property
    def stock_status(self):
        """Return stock status as a string"""
        if not self.available:
            return "outofstock"
        elif self.stock <= 0:
            return "outofstock"
        elif self.stock <= 5:
            return "low"
        else:
            return "instock"

    @property
    def get_category_display_name(self):
        """Return the human-readable category name"""
        return self.category.name if hasattr(self, 'category') and self.category else "Unknown Category"

    @property
    def is_shrimp_product(self):
        """
        Determine if this product is a shrimp product that requires special shipping (£12)
        Returns True for LIVE shrimp/fish only, False for food and equipment (£6)
        
        Aquarium Shop Context:
        - LIVE aquarium shrimp and fish need special shipping (£12) - temperature controlled, expedited
        - Food (frozen/dry), equipment, decorations use standard shipping (£6)
        """
        # Live aquarium animals that need special temperature-controlled shipping
        live_animal_terms = [
            'shrimp', 'cherry shrimp', 'ghost shrimp', 'amano shrimp',
            'crystal shrimp', 'bee shrimp', 'blue shrimp', 'red shrimp',
            'dwarf shrimp', 'freshwater shrimp', 'aquarium shrimp',
            'live shrimp', 'breeding shrimp',
            'fish', 'tetra', 'guppy', 'molly', 'platy', 'angelfish',
            'barb', 'danio', 'rasbora', 'corydoras', 'pleco',
            'live fish', 'tropical fish', 'freshwater fish',
            'snails', 'live snails', 'nerite snail', 'mystery snail',
            'crab', 'crayfish', 'live aquatic animals', 'livestock'
        ]
        
        product_name_lower = self.name.lower()
        category_name_lower = self.category.name.lower() if self.category else ''
        combined_text = product_name_lower + ' ' + category_name_lower
        
        # Check for live animals (these need special shipping)
        for term in live_animal_terms:
            if term in combined_text:
                # But exclude food items that might contain these terms
                food_indicators = ['food', 'flake', 'pellet', 'frozen', 'dried', 'treat']
                is_food = any(food_term in combined_text for food_term in food_indicators)
                if not is_food:
                    return True
        
        # Special case: specifically check for "live" animals
        if 'live' in combined_text:
            # This is likely a live animal
            return True
        
        return False

class Order(models.Model):
    """
    Model representing a customer order
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE, null=True, blank=True)
    stripe_checkout_id = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    payment_date = models.DateTimeField(null=True, blank=True)

    # Shipping information
    shipping_name = models.CharField(max_length=255, null=True, blank=True)
    shipping_address = models.TextField(null=True, blank=True)
    shipping_city = models.CharField(max_length=100, null=True, blank=True)
    shipping_state = models.CharField(max_length=100, null=True, blank=True)
    shipping_zip = models.CharField(max_length=20, null=True, blank=True)
    shipping_country = models.CharField(max_length=100, null=True, blank=True, default="United Kingdom")
    shipping_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(r'^\+?\d{7,15}$', 'Enter a valid phone number.')]
    )

    # Separate internal reference from shipping tracking number
    order_reference = models.CharField(max_length=100, blank=True, unique=True)
    tracking_number = models.CharField(max_length=100, blank=True, help_text="Shipping carrier tracking number")
    notes = models.TextField(blank=True, help_text="Any special instructions or notes for this order")
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        indexes = [
            models.Index(fields=['status', 'created_at'], name='order_status_created_idx'),
            models.Index(fields=['user', 'status'], name='order_user_status_idx'),
            models.Index(fields=['email', 'status'], name='order_email_status_idx'),
        ]

    def __str__(self):
        return f"Order {self.order_reference or self.id} - {self.email} ({self.get_status_display()})"
        
    def save(self, *args, **kwargs):
        # Generate order reference if not set
        if not self.order_reference:
            self.order_reference = f"SSS-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total amount from items if not set or zero
        if self.total_amount == 0 and self.pk:
            self.total_amount = self.calculate_total()
            
        super().save(*args, **kwargs)
    
    def calculate_total(self):
        """Calculate order total from items"""
        if self.pk:
            total = self.items.aggregate(
                total=Sum(F('quantity') * F('price'))
            )['total'] or Decimal('0.00')
            return total
        return Decimal('0.00')
        
    def update_totals(self):
        """Update order total based on current items"""
        self.total_amount = self.calculate_total()
        self.save(update_fields=['total_amount'])
        
    def get_absolute_url(self):
        """Return the URL for this order's detail page"""
        return reverse('store:order_detail', args=[self.order_reference])
        
    @property
    def formatted_total(self):
        """Return the total amount formatted with £ symbol"""
        return f"£{self.total_amount}"
        
    @property
    def item_count(self):
        """Return the total number of items in the order"""
        return self.items.aggregate(count=Sum('quantity'))['count'] or 0
        
    @property
    def shipping_complete(self):
        """Check if shipping information is complete"""
        return all([
            self.shipping_name,
            self.shipping_address,
            self.shipping_city,
            self.shipping_zip,
            self.shipping_country
        ])
    
    @property
    def total_price(self):
        """
        Alias for total_amount to maintain backward compatibility with views
        that might still reference total_price
        """
        return self.total_amount
        
    def clean(self):
        """Validate order data"""
        from django.core.exceptions import ValidationError
        
        # If status is shipped or delivered, require tracking number
        if self.status in ('shipped', 'delivered') and not self.tracking_number:
            raise ValidationError({'tracking_number': 'Tracking number is required for shipped/delivered orders'})
            
        super().clean()
        
    def get_shipping_address_display(self):
        """Return formatted shipping address"""
        parts = []
        if self.shipping_name:
            parts.append(self.shipping_name)
        if self.shipping_address:
            parts.append(self.shipping_address)
        if self.shipping_city:
            parts.append(self.shipping_city)
        if self.shipping_state:
            parts.append(self.shipping_state)
        if self.shipping_zip:
            parts.append(self.shipping_zip)
        if self.shipping_country:
            parts.append(self.shipping_country)
        return ', '.join(parts)

class OrderItem(models.Model):
    """Model representing an item within an order"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )  # Price at time of order
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True, null=True)  # Size at time of order
    
    class Meta:
        indexes = [
            models.Index(fields=["order", "product"], name="order_item_prod_idx"),
            models.Index(fields=["product", "size"], name="order_item_prod_size_idx"),
        ]
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'product', 'size'],
                name='unique_order_product_size'
            )
        ]
    
    def __str__(self):
        size_str = f" ({self.get_size_display()})" if self.size else ""
        return f"{self.quantity}x {self.product.name}{size_str} in Order {self.order.order_reference}"
    
    def clean(self):
        """Validate order item data"""
        from django.core.exceptions import ValidationError
        
        # Ensure quantity is reasonable
        if self.quantity and self.quantity > 999:
            raise ValidationError({'quantity': 'Quantity cannot exceed 999 items'})
        
        # Ensure price is reasonable
        if self.price and self.price > Decimal('9999.99'):
            raise ValidationError({'price': 'Item price cannot exceed £9,999.99'})
        
        super().clean()
    
    @property
    def subtotal(self):
        return self.price * self.quantity