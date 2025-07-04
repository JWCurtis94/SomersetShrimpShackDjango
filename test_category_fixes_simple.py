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
    
    # Create categories with specific orders
    categories = []
    for i in range(3):
        category = Category.objects.create(
            name=f"Order Test Category {i}",
            description=f"Test category {i}",
            order=(i + 1) * 10  # 10, 20, 30
        )
        categories.append(category)
    
    # Test ordering
    ordered_categories = list(Category.objects.filter(name__icontains="order test").order_by('order'))
    
    if len(ordered_categories) == 3:
        correct_order = True
        for i, cat in enumerate(ordered_categories):
            expected_order = (i + 1) * 10  # 10, 20, 30
            if cat.order != expected_order:
                correct_order = False
                print(f"  Category {i}: expected order {expected_order}, got {cat.order}")
                break
        
        if correct_order:
            print("✓ Category ordering works correctly")
        else:
            print("✗ Category ordering failed - wrong order")
    else:
        print(f"✗ Expected 3 categories, got {len(ordered_categories)}")
        for cat in ordered_categories:
            print(f"  Found: {cat.name} (order: {cat.order})")

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
            order=(i + 1) * 10  # 10, 20, 30
        )
        categories.append(category)
    
    # Simulate reordering by directly updating order values
    try:
        # Manually set specific orders to test reordering
        # Category 0: 10 -> 30 (last position)
        # Category 1: 20 -> 10 (first position) 
        # Category 2: 30 -> 20 (middle position)
        
        cat0 = Category.objects.get(name="Update Test Category 0")
        cat1 = Category.objects.get(name="Update Test Category 1")
        cat2 = Category.objects.get(name="Update Test Category 2")
        
        cat0.order = 30
        cat0.save()
        
        cat1.order = 10
        cat1.save()
        
        cat2.order = 20
        cat2.save()
        
        # Check new order - should be Category 1, Category 2, Category 0
        reordered = list(Category.objects.filter(name__icontains="update test").order_by('order'))
        expected_names = [
            "Update Test Category 1",  # order 10
            "Update Test Category 2",  # order 20
            "Update Test Category 0",  # order 30
        ]
        
        actual_names = [cat.name for cat in reordered]
        
        if actual_names == expected_names:
            print("✓ Category order update works correctly")
        else:
            print(f"✗ Category order update failed. Expected: {expected_names}, Got: {actual_names}")
            print("Details:")
            for cat in reordered:
                print(f"  {cat.name}: order = {cat.order}")
    
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
