from django.core.management.base import BaseCommand
from store.models import Category

class Command(BaseCommand):
    help = 'Set default order values for existing categories'

    def handle(self, *args, **options):
        categories = Category.objects.all().order_by('name')
        
        self.stdout.write(f"Found {categories.count()} categories")
        
        for i, category in enumerate(categories):
            # Set order based on alphabetical order, starting from 1
            category.order = (i + 1) * 10  # Use multiples of 10 to leave room for reordering
            category.save()
            self.stdout.write(f"Set {category.name} order to {category.order}")
        
        self.stdout.write(self.style.SUCCESS(f'Successfully set order values for {categories.count()} categories'))
        self.stdout.write("Categories are now ordered and ready for reordering in the admin interface!")
