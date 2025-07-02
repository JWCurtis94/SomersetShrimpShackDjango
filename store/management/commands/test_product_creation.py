from django.core.management.base import BaseCommand
from store.models import Product, Category
from decimal import Decimal

class Command(BaseCommand):
    help = 'Test product creation to debug 500 errors'

    def handle(self, *args, **options):
        try:
            # Get or create a test category
            category, created = Category.objects.get_or_create(
                name='Test Category',
                defaults={'slug': 'test-category', 'order': 0}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created test category: {category.name}'))
            
            # Try to create a test product
            product = Product(
                name='Test Product',
                category=category,
                price=Decimal('10.99'),
                stock=10,
                description='This is a test product',
                available=True
            )
            
            # Call full_clean to trigger validation
            product.full_clean()
            
            # Save the product
            product.save()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully created product: {product.name} (ID: {product.id})'))
            
            # Clean up
            product.delete()
            if created:
                category.delete()
            
            self.stdout.write(self.style.SUCCESS('Test completed successfully - no issues found'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during product creation test: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
