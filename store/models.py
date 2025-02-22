from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.utils.text import slugify
from decimal import Decimal
from django.utils import timezone

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

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField(blank=True)
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO meta description")
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    image = models.ImageField(
        upload_to='products/%Y/%m/',  # Organize by year/month
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp'])]
    )
    stock = models.PositiveIntegerField(default=0)  # Changed to PositiveIntegerField
    available = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'available']),
            models.Index(fields=['price', 'available']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Handle duplicate slugs
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{slugify(self.name)}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        return self.stock > 0 and self.available

class OrderItem(models.Model):
    order = models.ForeignKey('Order', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=['order', 'product']),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        return self.quantity * self.price

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE, null=True, blank=True)
    stripe_checkout_id = models.CharField(max_length=255, unique=True)
    email = models.EmailField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Shipping information
    shipping_name = models.CharField(max_length=255, null=True, blank=True)
    shipping_address = models.TextField(null=True, blank=True)
    shipping_city = models.CharField(max_length=100, null=True, blank=True)
    shipping_state = models.CharField(max_length=100, null=True, blank=True)
    shipping_zip = models.CharField(max_length=20, null=True, blank=True)
    shipping_country = models.CharField(max_length=100, null=True, blank=True)
    shipping_phone = models.CharField(max_length=20, blank=True, null=True)

    # Additional fields
    notes = models.TextField(blank=True)  # For customer or admin notes
    tracking_number = models.CharField(max_length=100, blank=True)  # For shipment tracking

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"Order {self.id} - {self.email} ({self.status})"

    @property
    def shipping_address_full(self):
        return f"{self.shipping_name}\n{self.shipping_address}\n{self.shipping_city}, {self.shipping_state} {self.shipping_zip}\n{self.shipping_country}"