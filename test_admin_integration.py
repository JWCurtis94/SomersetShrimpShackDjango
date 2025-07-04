"""
Test admin interface functionality for categories
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
from django.urls import reverse
from store.models import Category
from store.admin import CategoryAdmin
from django.contrib.admin.sites import site

def test_admin_integration():
    """Test that admin integration works correctly"""
    print("Testing admin integration...")
    
    # Create test user
    user = User.objects.create_superuser(
        username='testadmin',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create test categories
    categories = []
    for i in range(3):
        category = Category.objects.create(
            name=f"Admin Test Category {i}",
            description=f"Test category {i}",
            order=i * 10
        )
        categories.append(category)
    
    # Test admin functionality
    admin = CategoryAdmin(Category, site)
    
    # Test queryset ordering
    queryset = admin.get_queryset(request=None)
    ordered_categories = list(queryset.filter(name__icontains="admin test"))
    
    if len(ordered_categories) == 3:
        correct_order = True
        for i, cat in enumerate(ordered_categories):
            if cat.order != i * 10:
                correct_order = False
                break
        
        if correct_order:
            print("✓ Admin queryset ordering works correctly")
        else:
            print("✗ Admin queryset ordering failed")
    else:
        print(f"✗ Expected 3 categories, got {len(ordered_categories)}")
    
    # Test admin methods
    test_category = categories[0]
    
    # Test product_count method
    product_count = admin.product_count(test_category)
    if product_count == 0:  # Should be 0 since no products are linked
        print("✓ Admin product_count method works")
    else:
        print(f"✗ Admin product_count method failed: got {product_count}")
    
    # Test has_image method
    has_image = admin.has_image(test_category)
    if has_image is False:  # Should be False since no image is set
        print("✓ Admin has_image method works")
    else:
        print(f"✗ Admin has_image method failed: got {has_image}")
    
    # Clean up
    Category.objects.filter(name__icontains="admin test").delete()
    User.objects.filter(username='testadmin').delete()
    
    print("✓ Admin integration test completed")

def test_category_management_views():
    """Test category management views"""
    print("\nTesting category management views...")
    
    # Create test user
    user = User.objects.create_superuser(
        username='teststaff',
        email='staff@example.com',
        password='testpass123'
    )
    
    # Create test client
    client = Client()
    client.login(username='teststaff', password='testpass123')
    
    # Test category management page
    try:
        response = client.get(reverse('store:category_management'))
        if response.status_code == 200:
            print("✓ Category management page loads successfully")
        else:
            print(f"✗ Category management page failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Category management page error: {e}")
    
    # Test add category page
    try:
        response = client.get(reverse('store:add_category'))
        if response.status_code == 200:
            print("✓ Add category page loads successfully")
        else:
            print(f"✗ Add category page failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Add category page error: {e}")
    
    # Test creating a category via form
    try:
        response = client.post(reverse('store:add_category'), {
            'name': 'View Test Category',
            'description': 'Test category from view',
            'order': 10
        })
        if response.status_code == 302:  # Should redirect on success
            print("✓ Category creation via form works")
            
            # Check if category was created
            if Category.objects.filter(name='View Test Category').exists():
                print("✓ Category was saved to database")
            else:
                print("✗ Category was not saved to database")
        else:
            print(f"✗ Category creation failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Category creation error: {e}")
    
    # Test editing a category
    try:
        category = Category.objects.filter(name='View Test Category').first()
        if category:
            response = client.get(reverse('store:edit_category', args=[category.id]))
            if response.status_code == 200:
                print("✓ Edit category page loads successfully")
                
                # Test updating the category
                response = client.post(reverse('store:edit_category', args=[category.id]), {
                    'name': 'Updated View Test Category',
                    'description': 'Updated test category',
                    'order': 20
                })
                if response.status_code == 302:
                    print("✓ Category update via form works")
                    
                    # Check if category was updated
                    updated_category = Category.objects.get(id=category.id)
                    if updated_category.name == 'Updated View Test Category':
                        print("✓ Category was updated in database")
                    else:
                        print("✗ Category was not updated properly")
                else:
                    print(f"✗ Category update failed: {response.status_code}")
            else:
                print(f"✗ Edit category page failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Edit category error: {e}")
    
    # Clean up
    Category.objects.filter(name__icontains="view test").delete()
    User.objects.filter(username='teststaff').delete()
    
    print("✓ Category management views test completed")

def test_update_category_order_ajax():
    """Test AJAX category order update"""
    print("\nTesting AJAX category order update...")
    
    # Create test user
    user = User.objects.create_superuser(
        username='testajax',
        email='ajax@example.com',
        password='testpass123'
    )
    
    # Create test categories
    categories = []
    for i in range(3):
        category = Category.objects.create(
            name=f"AJAX Test Category {i}",
            description=f"Test category {i}",
            order=i * 10
        )
        categories.append(category)
    
    # Create test client
    client = Client()
    client.login(username='testajax', password='testpass123')
    
    # Test AJAX order update
    try:
        import json
        
        # Prepare order update data
        order_data = {
            'categories': [
                {'id': categories[0].id, 'order': 20},
                {'id': categories[1].id, 'order': 0},
                {'id': categories[2].id, 'order': 10}
            ]
        }
        
        response = client.post(
            reverse('store:update_category_order'),
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            response_data = json.loads(response.content)
            if response_data.get('success'):
                print("✓ AJAX category order update successful")
                
                # Verify the order was updated
                updated_categories = list(Category.objects.filter(name__icontains="ajax test").order_by('order'))
                expected_order = [categories[1].id, categories[2].id, categories[0].id]
                actual_order = [cat.id for cat in updated_categories]
                
                if actual_order == expected_order:
                    print("✓ Category order was updated correctly")
                else:
                    print(f"✗ Category order incorrect. Expected: {expected_order}, Got: {actual_order}")
            else:
                print(f"✗ AJAX response indicates failure: {response_data.get('message')}")
        else:
            print(f"✗ AJAX request failed: {response.status_code}")
    except Exception as e:
        print(f"✗ AJAX category order update error: {e}")
    
    # Clean up
    Category.objects.filter(name__icontains="ajax test").delete()
    User.objects.filter(username='testajax').delete()
    
    print("✓ AJAX category order update test completed")

if __name__ == "__main__":
    print("Somerset Shrimp Shack - Admin Integration Test")
    print("=" * 50)
    
    test_admin_integration()
    test_category_management_views()
    test_update_category_order_ajax()
    
    print("\n" + "=" * 50)
    print("Admin integration test completed!")
