from django.core.management.base import BaseCommand
from store.models import Product, Category
from decimal import Decimal
import logging

class Command(BaseCommand):
    help = 'Debug product creation issues in production'

    def handle(self, *args, **options):
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        try:
            self.stdout.write("=== Product Creation Debug ===")
            
            # Check if categories exist
            categories = Category.objects.all()
            self.stdout.write(f"Total categories: {categories.count()}")
            
            if categories.exists():
                category = categories.first()
                self.stdout.write(f"Using category: {category.name}")
            else:
                self.stdout.write("No categories found - creating test category")
                category = Category.objects.create(
                    name='Debug Category',
                    slug='debug-category',
                    order=0
                )
            
            # Check media/upload directories
            import os
            from django.conf import settings
            
            self.stdout.write(f"MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'Not set')}")
            self.stdout.write(f"MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'Not set')}")
            
            # Check if using AWS S3
            if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'):
                self.stdout.write(f"Using AWS S3: {settings.AWS_STORAGE_BUCKET_NAME}")
            
            # Try creating a minimal product
            self.stdout.write("Attempting to create test product...")
            
            product_data = {
                'name': 'Debug Test Product',
                'category': category,
                'price': Decimal('9.99'),
                'stock': 5,
                'description': 'Test product for debugging',
                'available': True
            }
            
            product = Product(**product_data)
            
            # Validate before saving
            self.stdout.write("Running validation...")
            product.full_clean()
            self.stdout.write("Validation passed")
            
            # Save the product
            self.stdout.write("Saving product...")
            product.save()
            self.stdout.write(f"Product saved successfully with ID: {product.id}")
            
            # Clean up
            product.delete()
            self.stdout.write("Test product deleted")
            
            self.stdout.write(self.style.SUCCESS("=== Debug completed successfully ==="))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            logger.exception("Product creation debug failed")
