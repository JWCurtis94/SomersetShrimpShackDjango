#!/usr/bin/env python
"""
Test script to diagnose image upload issues for categories and products
"""
import os
import django
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
import io

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Category, Product
from store.forms import CategoryForm, ProductForm

def create_test_image():
    """Create a test image file"""
    print("Creating test image...")
    
    # Create a simple test image
    image = Image.new('RGB', (100, 100), color='red')
    image_io = io.BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    
    # Create uploaded file
    uploaded_file = SimpleUploadedFile(
        name='test_image.jpg',
        content=image_io.getvalue(),
        content_type='image/jpeg'
    )
    
    return uploaded_file

def test_media_settings():
    """Test media settings configuration"""
    print("=== Testing Media Settings ===")
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"USE_S3: {getattr(settings, 'USE_S3', False)}")
    
    # Check if media directory exists
    if os.path.exists(settings.MEDIA_ROOT):
        print(f"✓ Media directory exists at: {settings.MEDIA_ROOT}")
    else:
        print(f"✗ Media directory missing at: {settings.MEDIA_ROOT}")
        try:
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            print(f"✓ Created media directory at: {settings.MEDIA_ROOT}")
        except Exception as e:
            print(f"✗ Failed to create media directory: {e}")
    
    # Check subdirectories
    categories_dir = os.path.join(settings.MEDIA_ROOT, 'categories')
    products_dir = os.path.join(settings.MEDIA_ROOT, 'products')
    
    for directory in [categories_dir, products_dir]:
        if os.path.exists(directory):
            print(f"✓ Directory exists: {directory}")
        else:
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"✓ Created directory: {directory}")
            except Exception as e:
                print(f"✗ Failed to create directory {directory}: {e}")

def test_category_image_upload():
    """Test category image upload"""
    print("\n=== Testing Category Image Upload ===")
    
    try:
        # Create a test image
        test_image = create_test_image()
        
        # Test form validation
        form_data = {
            'name': 'Test Category with Image',
            'description': 'Test category description',
            'order': 10
        }
        
        form = CategoryForm(data=form_data, files={'image': test_image})
        
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            return False
        
        # Save the category
        category = form.save()
        print(f"✓ Category created: {category.name}")
        print(f"✓ Category ID: {category.id}")
        print(f"✓ Image field: {category.image}")
        
        if category.image:
            print(f"✓ Image path: {category.image.name}")
            print(f"✓ Image URL: {category.image.url}")
            
            # Check if file exists
            full_path = os.path.join(settings.MEDIA_ROOT, category.image.name)
            if os.path.exists(full_path):
                print(f"✓ Image file exists at: {full_path}")
                print(f"✓ File size: {os.path.getsize(full_path)} bytes")
            else:
                print(f"✗ Image file missing at: {full_path}")
        else:
            print("✗ No image saved to category")
            
        return True
        
    except Exception as e:
        print(f"✗ Category image upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_product_image_upload():
    """Test product image upload"""
    print("\n=== Testing Product Image Upload ===")
    
    try:
        # First ensure we have a category
        category, created = Category.objects.get_or_create(
            name='Test Category',
            defaults={'description': 'Test category for products', 'order': 10}
        )
        
        # Create a test image
        test_image = create_test_image()
        
        # Test form validation
        form_data = {
            'name': 'Test Product with Image',
            'description': 'Test product description',
            'price': '19.99',
            'category': category.id,
            'stock': 10,
            'available': True,
            'featured': False
        }
        
        form = ProductForm(data=form_data, files={'image': test_image})
        
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            return False
        
        # Save the product
        product = form.save()
        print(f"✓ Product created: {product.name}")
        print(f"✓ Product ID: {product.id}")
        print(f"✓ Image field: {product.image}")
        
        if product.image:
            print(f"✓ Image path: {product.image.name}")
            print(f"✓ Image URL: {product.image.url}")
            
            # Check if file exists
            full_path = os.path.join(settings.MEDIA_ROOT, product.image.name)
            if os.path.exists(full_path):
                print(f"✓ Image file exists at: {full_path}")
                print(f"✓ File size: {os.path.getsize(full_path)} bytes")
            else:
                print(f"✗ Image file missing at: {full_path}")
        else:
            print("✗ No image saved to product")
            
        return True
        
    except Exception as e:
        print(f"✗ Product image upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_admin_integration():
    """Test admin interface integration"""
    print("\n=== Testing Admin Integration ===")
    
    try:
        # Test category creation via model save
        test_image = create_test_image()
        
        category = Category(
            name='Admin Test Category',
            description='Test category created via admin',
            order=20
        )
        category.image = test_image
        category.save()
        
        print(f"✓ Category saved via admin: {category.name}")
        if category.image:
            print(f"✓ Image saved: {category.image.name}")
            full_path = os.path.join(settings.MEDIA_ROOT, category.image.name)
            if os.path.exists(full_path):
                print(f"✓ Image file exists: {full_path}")
            else:
                print(f"✗ Image file missing: {full_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Admin integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning up test data ===")
    
    try:
        # Delete test categories and products
        Category.objects.filter(name__icontains='Test').delete()
        Product.objects.filter(name__icontains='Test').delete()
        print("✓ Test data cleaned up")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")

if __name__ == "__main__":
    print("Testing Image Upload Functionality")
    print("=" * 50)
    
    # Test media settings
    test_media_settings()
    
    # Test category image upload
    category_success = test_category_image_upload()
    
    # Test product image upload
    product_success = test_product_image_upload()
    
    # Test admin integration
    admin_success = test_admin_integration()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Category upload: {'✓ PASS' if category_success else '✗ FAIL'}")
    print(f"Product upload: {'✓ PASS' if product_success else '✗ FAIL'}")
    print(f"Admin integration: {'✓ PASS' if admin_success else '✗ FAIL'}")
    
    if not all([category_success, product_success, admin_success]):
        print("\n⚠️  Some tests failed. Check the errors above.")
    else:
        print("\n✓ All tests passed!")
    
    # Cleanup
    cleanup_test_data()
