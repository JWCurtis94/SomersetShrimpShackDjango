"""
Debug the auto-assignment issue
"""
import os
import django
import sys

# Add the project directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Category

def debug_category_creation():
    """Debug category creation with auto-assignment"""
    print("Debugging category auto-assignment...")
    
    # Clean up
    Category.objects.filter(name__icontains="debug test").delete()
    
    # Create categories and see what orders they get
    for i in range(3):
        category = Category(
            name=f"Debug Test Category {i}",
            description=f"Test category {i}"
        )
        print(f"Before save - Category {i}: order = {category.order}")
        
        category.save()
        
        print(f"After save - Category {i}: order = {category.order}")
        print(f"  Next order would be: {category.get_next_order()}")
    
    # Show final ordering
    categories = Category.objects.filter(name__icontains="debug test").order_by('order')
    print("\nFinal order:")
    for cat in categories:
        print(f"  {cat.name}: order = {cat.order}")
    
    # Clean up
    Category.objects.filter(name__icontains="debug test").delete()

if __name__ == "__main__":
    debug_category_creation()
