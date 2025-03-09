from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, RegexValidator
from django.utils.text import slugify
from django.db.models import Sum, F
from decimal import Decimal
import uuid

# Function to generate unique slug
def generate_unique_slug(instance):
    base_slug = slugify(instance.name)
    slug = base_slug
    counter = 1
    
    # Handle updating existing products correctly
    if instance.pk:
        query = Product.objects.filter(slug=slug).exclude(pk=instance.pk)
    else:
        query = Product.objects.filter(slug=slug)
    
    while query.exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
        if instance.pk:
            query = Product.objects.filter(slug=slug).exclude(pk=instance.pk)
        else:
            query = Product.objects.filter(slug=slug)
    return slug

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('neocaridina', 'Neocaridina Shrimp'),
        ('caridina', 'Caridina Shrimp'),
        ('floating_plants', 'Floating Plants'),
        ('stem_plants', 'Stem Plants'),
        ('rosette_plants', 'Rosette Plants'),
        ('botanicals', 'Botanicals'),
        ('food', 'Food'),
        ('merchandise', 'Merchandise'),
    ]
    
    SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField(blank=True)
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO meta description")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    # Added size field for products that come in different sizes (like shrimp)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, blank=True, null=True)
    image = models.ImageField(
        upload_to='products/%Y/%m/',  
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    stock = models.IntegerField(default=0)  
    available = models.BooleanField(default=True, db_index=True)
    featured = models.BooleanField(default=False, help_text="Feature this product on the homepage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'available']),
            models.Index(fields=['price', 'available']),
            models.Index(fields=['featured', 'available']),
            models.Index(fields=['size', 'category']),
        ]
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug:
            self.slug = generate_unique_slug(self)
            
        # Auto-update available status based on stock
        self.available = self.stock > 0
        
        super().save(*args, **kwargs)

    def __str__(self):
        if self.size:
            return f"{self.name} - {self.get_size_display()}"
        return self.name

    @property
    def is_in_stock(self):
        return self.stock > 0 and self.available
        
    @property
    def display_price(self):
        """Return price formatted for display with £ symbol"""
        return f"£{self.price}"
        
    @property
    def stock_status(self):
        """Return stock status as a string"""
        if not self.available or self.stock <= 0:
            return "outofstock"
        elif self.stock <= 5:
            return "low"
        else:
            return "instock"


class OrderItem(models.Model):
    order = models.ForeignKey('Order', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['order', 'product']),
        ]
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        size_str = f" ({self.size})" if self.size else ""
        return f"{self.quantity}x {self.product.name}{size_str}"

    @property
    def subtotal(self):
        return Decimal(self.quantity) * self.price
        
    def save(self, *args, **kwargs):
        # Make sure price is set from product if not specified
        if not self.price and self.product:
            self.price = self.product.price
        super().save(*args, **kwargs)
        
        # Update order total when item is saved or updated
        if self.order:
            self.order.update_totals()


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE, null=True, blank=True)
    stripe_checkout_id = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
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
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['email', 'status']),
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