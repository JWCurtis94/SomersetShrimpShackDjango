#!/usr/bin/env python
"""
Test admin interface image upload functionality
"""
import os
import django

# Setup Django BEFORE importing anything else
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

from store.models import Category, Product
from store.admin import CategoryAdmin, ProductAdmin

def create_test_image():
    """Create a test image file"""
    image = Image.new('RGB', (150, 150), color='green')
    image_io = io.BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    
    uploaded_file = SimpleUploadedFile(
        name='admin_test_image.jpg',
        content=image_io.getvalue(),
        content_type='image/jpeg'
    )
    
    return uploaded_file

def test_category_admin():
    """Test category admin with image upload"""
    print("Testing Category Admin Image Upload")
    print("=" * 40)
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.post('/admin/store/category/add/')
    
    # Get or create a superuser for the request
    user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={'email': 'admin@test.com', 'is_superuser': True, 'is_staff': True}
    )
    if created:
        user.set_password('password')
        user.save()
    
    request.user = user
    
    # Create admin instance
    admin_site = AdminSite()
    category_admin = CategoryAdmin(Category, admin_site)
    
    # Create test data
    test_image = create_test_image()
    category = Category(
        name='Admin Test Category',
        description='Testing admin image upload',
        image=test_image
    )
    
    try:
        # Test the admin's save_model method
        category_admin.save_model(request, category, None, False)
        print(f"✓ Category saved via admin: {category.name}")
        print(f"✓ Category ID: {category.id}")
        print(f"✓ Image URL: {category.image.url}")
        
        # Clean up
        category.delete()
        # Don't delete user as it might be reused
        
        return True
        
    except Exception as e:
        print(f"✗ Admin save failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_product_admin():
    """Test product admin with image upload"""
    print("\nTesting Product Admin Image Upload")
    print("=" * 40)
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.post('/admin/store/product/add/')
    
    # Get or create a superuser for the request
    user, created = User.objects.get_or_create(
        username='admin_test2',
        defaults={'email': 'admin2@test.com', 'is_superuser': True, 'is_staff': True}
    )
    if created:
        user.set_password('password')
        user.save()
    
    request.user = user
    
    # Create admin instance
    admin_site = AdminSite()
    product_admin = ProductAdmin(Product, admin_site)
    
    # Create test category first
    category = Category.objects.create(
        name='Test Category for Product',
        description='Test category'
    )
    
    # Create test data
    test_image = create_test_image()
    product = Product(
        name='Admin Test Product',
        description='Testing admin image upload',
        price=25.99,
        category=category,
        stock=10,
        image=test_image
    )
    
    try:
        # Test the admin's save_model method
        product_admin.save_model(request, product, None, False)
        print(f"✓ Product saved via admin: {product.name}")
        print(f"✓ Product ID: {product.id}")
        print(f"✓ Image URL: {product.image.url}")
        
        # Clean up
        product.delete()
        category.delete()
        # Don't delete user as it might be reused
        
        return True
        
    except Exception as e:
        print(f"✗ Admin save failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Admin Interface Image Upload")
    print("=" * 50)
    
    category_success = test_category_admin()
    product_success = test_product_admin()
    
    print("\n" + "=" * 50)
    print("Admin Test Summary:")
    print(f"Category admin: {'✓ PASS' if category_success else '✗ FAIL'}")
    print(f"Product admin: {'✓ PASS' if product_success else '✗ FAIL'}")
    
    if category_success and product_success:
        print("\n✓ All admin tests passed!")
    else:
        print("\n⚠️  Some admin tests failed.")
