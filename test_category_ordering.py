"""
Test script to verify category ordering is working
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

def test_category_ordering():
    """Test that categories are ordered correctly"""
    print("Testing category ordering...")
    
    # Get all categories ordered by order field
    categories = Category.objects.all().order_by('order', 'name')
    
    print(f"Found {categories.count()} categories:")
    for i, category in enumerate(categories):
        print(f"  {i+1}. {category.name} (order: {category.order}, slug: {category.slug})")
    
    # Test context processor
    from store.context_processors import categories_context
    
    class MockRequest:
        pass
    
    context = categories_context(MockRequest())
    nav_categories = context['nav_categories']
    
    print(f"\nContext processor returns {nav_categories.count()} categories:")
    for i, category in enumerate(nav_categories):
        print(f"  {i+1}. {category.name} (order: {category.order})")

if __name__ == "__main__":
    test_category_ordering()
