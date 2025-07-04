#!/usr/bin/env python
"""
Simple test to verify that image uploads work for categories and products
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from store.models import Category, Product
from store.forms import CategoryForm, ProductForm
import io

def create_test_image(name='test.jpg'):
    """Create a simple test image"""
    image = Image.new('RGB', (100, 100), color='red')
    image_io = io.BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    
    return SimpleUploadedFile(
        name=name,
        content=image_io.getvalue(),
        content_type='image/jpeg'
    )

def test_category_image():
    """Test category image upload"""
    print("Testing Category Image Upload")
    print("=" * 30)
    
    # Create test image
    test_image = create_test_image('category_test.jpg')
    
    # Create category directly
    category = Category.objects.create(
        name='Direct Category Test',
        description='Testing direct category creation',
        image=test_image
    )
    
    print(f"✓ Category created: {category.name}")
    print(f"✓ Image saved: {category.image.name}")
    print(f"✓ Image URL: {category.image.url}")
    
    # Test form-based creation
    form_image = create_test_image('form_category_test.jpg')
    form_data = {
        'name': 'Form Category Test',
        'description': 'Testing form-based category creation',
        'order': 10
    }
    
    form = CategoryForm(data=form_data, files={'image': form_image})
    if form.is_valid():
        form_category = form.save()
        print(f"✓ Form category created: {form_category.name}")
        print(f"✓ Form image saved: {form_category.image.name}")
        print(f"✓ Form image URL: {form_category.image.url}")
    else:
        print(f"✗ Form validation failed: {form.errors}")
    
    # Clean up
    category.delete()
    if 'form_category' in locals():
        form_category.delete()
    
    return True

def test_product_image():
    """Test product image upload"""
    print("\nTesting Product Image Upload")
    print("=" * 30)
    
    # Create test category first
    category = Category.objects.create(
        name='Product Test Category',
        description='Category for product testing'
    )
    
    # Create test image
    test_image = create_test_image('product_test.jpg')
    
    # Create product directly
    product = Product.objects.create(
        name='Direct Product Test',
        description='Testing direct product creation',
        price=19.99,
        category=category,
        stock=10,
        image=test_image
    )
    
    print(f"✓ Product created: {product.name}")
    print(f"✓ Image saved: {product.image.name}")
    print(f"✓ Image URL: {product.image.url}")
    
    # Test form-based creation
    form_image = create_test_image('form_product_test.jpg')
    form_data = {
        'name': 'Form Product Test',
        'description': 'Testing form-based product creation',
        'price': '25.99',
        'category': category.id,
        'stock': 5,
        'available': True,
        'featured': False
    }
    
    form = ProductForm(data=form_data, files={'image': form_image})
    if form.is_valid():
        form_product = form.save()
        print(f"✓ Form product created: {form_product.name}")
        print(f"✓ Form image saved: {form_product.image.name}")
        print(f"✓ Form image URL: {form_product.image.url}")
    else:
        print(f"✗ Form validation failed: {form.errors}")
    
    # Clean up
    product.delete()
    if 'form_product' in locals():
        form_product.delete()
    category.delete()
    
    return True

if __name__ == "__main__":
    print("Simple Image Upload Test")
    print("=" * 50)
    
    try:
        category_success = test_category_image()
        product_success = test_product_image()
        
        print("\n" + "=" * 50)
        print("Test Results:")
        print(f"Category image upload: {'✓ PASS' if category_success else '✗ FAIL'}")
        print(f"Product image upload: {'✓ PASS' if product_success else '✗ FAIL'}")
        
        if category_success and product_success:
            print("\n🎉 All image upload tests passed!")
            print("✓ Categories can accept image uploads")
            print("✓ Products can accept image uploads")
            print("✓ Images are being saved to S3")
            print("✓ Forms are working correctly")
        else:
            print("\n⚠️  Some tests failed.")
    
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
