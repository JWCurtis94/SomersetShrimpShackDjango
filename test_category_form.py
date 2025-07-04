#!/usr/bin/env python
"""
Test script to verify category form functionality
"""
import os
import sys
import django

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.forms import CategoryForm
from store.models import Category

def test_category_form():
    """Test the CategoryForm validation"""
    
    print("🧪 Testing CategoryForm...")
    print("-" * 40)
    
    # Test 1: Valid form data with all fields
    print("Test 1: Valid form with all fields")
    form_data = {
        'name': 'Test Category',
        'description': 'This is a test category',
        'order': 5
    }
    
    form = CategoryForm(data=form_data)
    if form.is_valid():
        print("✅ Form is valid with all fields")
        print(f"   Clean data: {form.cleaned_data}")
    else:
        print("❌ Form is invalid with all fields")
        print(f"   Errors: {form.errors}")
    
    # Test 2: Valid form data without order field
    print("\nTest 2: Valid form without order field")
    form_data_no_order = {
        'name': 'Test Category 2',
        'description': 'This is another test category',
    }
    
    form2 = CategoryForm(data=form_data_no_order)
    if form2.is_valid():
        print("✅ Form is valid without order field")
        print(f"   Clean data: {form2.cleaned_data}")
        print(f"   Order field value: {form2.cleaned_data.get('order', 'Not set')}")
    else:
        print("❌ Form is invalid without order field")
        print(f"   Errors: {form2.errors}")
    
    # Test 3: Form with only name (minimum required)
    print("\nTest 3: Form with only name")
    form_data_minimal = {
        'name': 'Minimal Category',
    }
    
    form3 = CategoryForm(data=form_data_minimal)
    if form3.is_valid():
        print("✅ Form is valid with only name")
        print(f"   Clean data: {form3.cleaned_data}")
    else:
        print("❌ Form is invalid with only name")
        print(f"   Errors: {form3.errors}")
    
    # Test 4: Form with empty name (should fail)
    print("\nTest 4: Form with empty name")
    form_data_empty = {
        'name': '',
        'description': 'Category without name',
        'order': 1
    }
    
    form4 = CategoryForm(data=form_data_empty)
    if form4.is_valid():
        print("❌ Form should not be valid with empty name")
        print(f"   Clean data: {form4.cleaned_data}")
    else:
        print("✅ Form correctly rejects empty name")
        print(f"   Errors: {form4.errors}")
    
    print("\n" + "=" * 40)
    print("📋 CATEGORY FORM TEST SUMMARY")
    print("=" * 40)
    
    # Check current categories
    category_count = Category.objects.count()
    print(f"Current categories in database: {category_count}")
    
    if category_count > 0:
        print("\nExisting categories:")
        for cat in Category.objects.all()[:5]:  # Show first 5
            print(f"  • {cat.name} (order: {cat.order})")
    
    print("\n🎯 KEY FINDINGS:")
    print("• Order field should be optional with default value")
    print("• Form should accept missing order field")
    print("• Name field is required")
    print("• Description field is optional")
    print("• Image field is optional")

if __name__ == '__main__':
    test_category_form()
