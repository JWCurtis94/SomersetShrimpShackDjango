#!/usr/bin/env python
"""
Test S3 image upload verification
"""
import os
import django
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Category, Product

def create_test_image():
    """Create a test image file"""
    image = Image.new('RGB', (200, 200), color='blue')
    image_io = io.BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    
    uploaded_file = SimpleUploadedFile(
        name='test_s3_image.jpg',
        content=image_io.getvalue(),
        content_type='image/jpeg'
    )
    
    return uploaded_file

def test_s3_upload():
    """Test S3 upload and verify URL accessibility"""
    print("Testing S3 Image Upload")
    print("=" * 40)
    
    # Create a test category with image
    test_image = create_test_image()
    category = Category.objects.create(
        name='S3 Test Category',
        description='Testing S3 image upload',
        image=test_image
    )
    
    print(f"Category created: {category.name}")
    print(f"Image URL: {category.image.url}")
    
    # Test if the URL is accessible
    try:
        response = requests.head(category.image.url, timeout=10)
        print(f"URL Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Image successfully uploaded to S3 and accessible")
        else:
            print(f"✗ Image not accessible (status: {response.status_code})")
    except Exception as e:
        print(f"✗ Error accessing URL: {e}")
    
    # Clean up
    category.delete()
    print("Test category deleted")

if __name__ == "__main__":
    test_s3_upload()
