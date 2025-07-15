"""
Management command to fix category ordering
"""
from django.core.management.base import BaseCommand
from store.models import Category

class Command(BaseCommand):
    help = 'Fix category ordering by setting proper order values'

    def handle(self, *args, **options):
        categories = Category.objects.all().order_by('name')
        
        self.stdout.write(f"Found {categories.count()} categories to fix")
        
        for i, category in enumerate(categories):
            old_order = category.order
            new_order = (i + 1) * 10  # Set orders as 10, 20, 30, etc.
            
            category.order = new_order
            category.save()
            
            self.stdout.write(
                f"Updated '{category.name}': {old_order} -> {new_order}"
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {categories.count()} categories')
        )
