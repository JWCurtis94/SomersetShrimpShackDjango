"""
Test script for category operations to verify fixes
"""
import os
import django
import sys

# Add the project directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from store.models import Category
from store.forms import CategoryForm
import tempfile
from PIL import Image
import io

def create_test_image():
    """Create a test image for upload testing"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    return SimpleUploadedFile('test.png', img_io.read(), content_type='image/png')

def test_category_creation():
    """Test category creation with various scenarios"""
    print("Testing category creation...")
    
    # Test 1: Valid category creation
    try:
        category = Category.objects.create(
            name="Test Category",
            description="Test description"
        )
        print(f"✓ Valid category created: {category.name} (slug: {category.slug})")
    except Exception as e:
        print(f"✗ Error creating valid category: {e}")
    
    # Test 2: Category with duplicate name
    try:
        Category.objects.create(
            name="Test Category",
            description="Another test description"
        )
        print("✗ Duplicate category created (should have failed)")
    except Exception as e:
        print(f"✓ Duplicate category rejected: {e}")
    
    # Test 3: Category with image
    try:
        test_image = create_test_image()
        category = Category.objects.create(
            name="Test Category With Image",
            description="Test description",
            image=test_image
        )
        print(f"✓ Category with image created: {category.name}")
    except Exception as e:
        print(f"✗ Error creating category with image: {e}")

def test_category_form():
    """Test CategoryForm validation"""
    print("\nTesting CategoryForm validation...")
    
    # Test 1: Valid form
    form_data = {
        'name': 'Form Test Category',
        'description': 'Test description',
        'order': 10
    }
    form = CategoryForm(data=form_data)
    if form.is_valid():
        print("✓ Valid form passed validation")
    else:
        print(f"✗ Valid form failed validation: {form.errors}")
    
    # Test 2: Empty name
    form_data = {
        'name': '',
        'description': 'Test description',
        'order': 10
    }
    form = CategoryForm(data=form_data)
    if not form.is_valid():
        print("✓ Empty name form rejected")
    else:
        print("✗ Empty name form accepted (should have failed)")
    
    # Test 3: Large image
    try:
        # Create a large image (simulate > 5MB)
        large_img = Image.new('RGB', (3000, 3000), color='blue')
        img_io = io.BytesIO()
        large_img.save(img_io, format='PNG')
        img_io.seek(0)
        large_image = SimpleUploadedFile('large.png', img_io.read(), content_type='image/png')
        
        form_data = {
            'name': 'Large Image Category',
            'description': 'Test description',
            'order': 10
        }
        form = CategoryForm(data=form_data, files={'image': large_image})
        if not form.is_valid():
            print("✓ Large image form rejected")
        else:
            print("✗ Large image form accepted (should have failed)")
    except Exception as e:
        print(f"Note: Large image test skipped: {e}")

def test_category_ordering():
    """Test category ordering functionality"""
    print("\nTesting category ordering...")
    
    # Create test categories
    categories = []
    for i in range(3):
        category = Category.objects.create(
            name=f"Order Test Category {i}",
            description=f"Test description {i}",
            order=i * 10
        )
        categories.append(category)
    
    # Test ordering
    ordered_categories = Category.objects.all().order_by('order')
    correct_order = True
    for i, cat in enumerate(ordered_categories):
        if cat.order != i * 10:
            correct_order = False
            break
    
    if correct_order:
        print("✓ Category ordering works correctly")
    else:
        print("✗ Category ordering failed")

def test_slug_generation():
    """Test unique slug generation"""
    print("\nTesting slug generation...")
    
    # Test 1: Basic slug generation
    category1 = Category.objects.create(
        name="Test Slug Category",
        description="Test description"
    )
    
    if category1.slug == "test-slug-category":
        print("✓ Basic slug generation works")
    else:
        print(f"✗ Basic slug generation failed: {category1.slug}")
    
    # Test 2: Duplicate slug handling
    category2 = Category.objects.create(
        name="Test Slug Category",  # Same name as category1
        description="Another test description"
    )
    
    if category2.slug != category1.slug:
        print(f"✓ Duplicate slug handling works: {category2.slug}")
    else:
        print(f"✗ Duplicate slug handling failed: {category2.slug}")

def cleanup_test_data():
    """Clean up test data"""
    print("\nCleaning up test data...")
    try:
        Category.objects.filter(name__startswith="Test").delete()
        Category.objects.filter(name__startswith="Form Test").delete()
        Category.objects.filter(name__startswith="Order Test").delete()
        print("✓ Test data cleaned up")
    except Exception as e:
        print(f"✗ Error cleaning up test data: {e}")

if __name__ == "__main__":
    print("Somerset Shrimp Shack - Category Fixes Test")
    print("=" * 50)
    
    try:
        test_category_creation()
        test_category_form()
        test_category_ordering()
        test_slug_generation()
    finally:
        cleanup_test_data()
    
    print("\n" + "=" * 50)
    print("Test completed!")
