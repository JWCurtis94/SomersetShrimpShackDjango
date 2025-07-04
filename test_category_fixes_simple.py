"""
Simple test to check category operations without complex image handling
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
from store.forms import CategoryForm
from django.core.exceptions import ValidationError

def test_category_duplicates():
    """Test category duplicate name prevention"""
    print("Testing category duplicate name prevention...")
    
    # Clean up any existing test data
    Category.objects.filter(name__icontains="duplicate test").delete()
    
    # Create first category
    try:
        category1 = Category.objects.create(
            name="Duplicate Test Category",
            description="First test category"
        )
        print(f"✓ First category created: {category1.name}")
    except Exception as e:
        print(f"✗ Error creating first category: {e}")
        return
    
    # Try to create duplicate
    try:
        category2 = Category.objects.create(
            name="Duplicate Test Category",
            description="Second test category"
        )
        print("✗ Duplicate category was created (should have failed)")
    except ValidationError as e:
        print(f"✓ Duplicate category rejected: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

def test_category_form_validation():
    """Test CategoryForm validation"""
    print("\nTesting CategoryForm validation...")
    
    # Test valid form
    form_data = {
        'name': 'Valid Form Category',
        'description': 'Test description',
        'order': 10
    }
    form = CategoryForm(data=form_data)
    if form.is_valid():
        print("✓ Valid form passes validation")
    else:
        print(f"✗ Valid form fails validation: {form.errors}")
    
    # Test empty name
    form_data = {
        'name': '',
        'description': 'Test description',
        'order': 10
    }
    form = CategoryForm(data=form_data)
    if not form.is_valid() and 'name' in form.errors:
        print("✓ Empty name form rejected")
    else:
        print(f"✗ Empty name form validation failed: {form.errors}")
    
    # Test whitespace-only name
    form_data = {
        'name': '   ',
        'description': 'Test description',
        'order': 10
    }
    form = CategoryForm(data=form_data)
    if not form.is_valid() and 'name' in form.errors:
        print("✓ Whitespace-only name form rejected")
    else:
        print(f"✗ Whitespace-only name form validation failed: {form.errors}")

def test_category_ordering():
    """Test category ordering"""
    print("\nTesting category ordering...")
    
    # Clean up existing test data
    Category.objects.filter(name__icontains="order test").delete()
    
    # Create categories with different orders
    categories = []
    for i in range(3):
        category = Category.objects.create(
            name=f"Order Test Category {i}",
            description=f"Test category {i}",
            order=i * 10
        )
        categories.append(category)
    
    # Test ordering
    ordered_categories = list(Category.objects.filter(name__icontains="order test").order_by('order'))
    
    if len(ordered_categories) == 3:
        correct_order = True
        for i, cat in enumerate(ordered_categories):
            expected_order = i * 10
            if cat.order != expected_order:
                correct_order = False
                break
        
        if correct_order:
            print("✓ Category ordering works correctly")
        else:
            print("✗ Category ordering failed - wrong order")
    else:
        print(f"✗ Expected 3 categories, got {len(ordered_categories)}")

def test_update_category_order_endpoint():
    """Test the update category order functionality"""
    print("\nTesting category order update...")
    
    # Create some test categories
    Category.objects.filter(name__icontains="update test").delete()
    
    categories = []
    for i in range(3):
        category = Category.objects.create(
            name=f"Update Test Category {i}",
            description=f"Test category {i}",
            order=i * 10
        )
        categories.append(category)
    
    # Simulate reordering
    try:
        # Change order of categories
        categories[0].order = 20
        categories[0].save()
        
        categories[1].order = 0
        categories[1].save()
        
        categories[2].order = 10
        categories[2].save()
        
        # Check new order
        reordered = list(Category.objects.filter(name__icontains="update test").order_by('order'))
        expected_names = [
            "Update Test Category 1",  # order 0
            "Update Test Category 2",  # order 10
            "Update Test Category 0",  # order 20
        ]
        
        actual_names = [cat.name for cat in reordered]
        
        if actual_names == expected_names:
            print("✓ Category order update works correctly")
        else:
            print(f"✗ Category order update failed. Expected: {expected_names}, Got: {actual_names}")
    
    except Exception as e:
        print(f"✗ Error testing category order update: {e}")

def cleanup():
    """Clean up test data"""
    print("\nCleaning up test data...")
    try:
        Category.objects.filter(name__icontains="test").delete()
        print("✓ Test data cleaned up")
    except Exception as e:
        print(f"✗ Error cleaning up: {e}")

if __name__ == "__main__":
    print("Somerset Shrimp Shack - Category Fixes Test (Simplified)")
    print("=" * 60)
    
    try:
        test_category_duplicates()
        test_category_form_validation()
        test_category_ordering()
        test_update_category_order_endpoint()
    finally:
        cleanup()
    
    print("\n" + "=" * 60)
    print("Test completed!")
