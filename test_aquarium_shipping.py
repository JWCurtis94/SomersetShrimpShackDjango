#!/usr/bin/env python
"""
Test shipping costs for aquarium store - verify £12 for live animals, £6 for non-live
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product
from store.cart import Cart
from django.http import HttpRequest
from decimal import Decimal

def test_shipping_costs():
    """Test that shipping costs are correctly applied"""
    print("Somerset Shrimp Shack - Shipping Cost Verification")
    print("=" * 55)
    
    # Create a simple mock session class
    class MockSession(dict):
        def __init__(self):
            super().__init__()
            self.modified = False
    
    # Create a mock request for cart
    request = HttpRequest()
    request.session = MockSession()
    
    # Test 1: Live animals only (should be £12)
    print("\n🧪 Test 1: Live Animals Only")
    cart1 = Cart(request)
    cart1.clear()  # Start fresh
    
    cherry_shrimp = Product.objects.get(slug='cherry-shrimp-red')
    nerite_snails = Product.objects.get(slug='nerite-snails')
    
    cart1.add(cherry_shrimp, quantity=5)
    cart1.add(nerite_snails, quantity=3)
    
    shipping1 = cart1.get_shipping_cost()
    print(f"Products: {cherry_shrimp.name} (Live), {nerite_snails.name} (Live)")
    print(f"Expected: £12.00 (live animals)")
    print(f"Actual: £{shipping1}")
    print(f"✅ Correct!" if shipping1 == Decimal('12.00') else f"❌ Wrong!")
    
    # Test 2: Non-live items only (should be £6)
    print("\n🧪 Test 2: Non-Live Items Only")
    cart2 = Cart(request)
    cart2.clear()
    
    java_moss = Product.objects.get(slug='java-moss')
    shrimp_food = Product.objects.get(slug='shrimp-pellets-premium')
    filter_item = Product.objects.get(slug='nano-aquarium-filter')
    
    cart2.add(java_moss, quantity=2)
    cart2.add(shrimp_food, quantity=1)
    cart2.add(filter_item, quantity=1)
    
    shipping2 = cart2.get_shipping_cost()
    print(f"Products: {java_moss.name}, {shrimp_food.name}, {filter_item.name}")
    print(f"Expected: £6.00 (non-live items)")
    print(f"Actual: £{shipping2}")
    print(f"✅ Correct!" if shipping2 == Decimal('6.00') else f"❌ Wrong!")
    
    # Test 3: Mixed cart (should be £12 - live animal shipping applies)
    print("\n🧪 Test 3: Mixed Cart (Live + Non-Live)")
    cart3 = Cart(request)
    cart3.clear()
    
    blue_shrimp = Product.objects.get(slug='blue-dream-shrimp')  # Live
    moss_balls = Product.objects.get(slug='marimo-moss-balls')   # Non-live
    heater = Product.objects.get(slug='aquarium-heater-25w')     # Non-live
    
    cart3.add(blue_shrimp, quantity=10)  # Live animal
    cart3.add(moss_balls, quantity=2)    # Plant
    cart3.add(heater, quantity=1)        # Equipment
    
    shipping3 = cart3.get_shipping_cost()
    print(f"Products: {blue_shrimp.name} (Live), {moss_balls.name}, {heater.name}")
    print(f"Expected: £12.00 (live animal shipping takes precedence)")
    print(f"Actual: £{shipping3}")
    print(f"✅ Correct!" if shipping3 == Decimal('12.00') else f"❌ Wrong!")
    
    # Test 4: Empty cart (should be £0)
    print("\n🧪 Test 4: Empty Cart")
    cart4 = Cart(request)
    cart4.clear()
    
    shipping4 = cart4.get_shipping_cost()
    print(f"Products: None (empty cart)")
    print(f"Expected: £0.00 (no shipping for empty cart)")
    print(f"Actual: £{shipping4}")
    print(f"✅ Correct!" if shipping4 == Decimal('0.00') else f"❌ Wrong!")
    
    # Summary
    print(f"\n📋 Shipping Rules Summary:")
    print(f"=" * 30)
    print(f"🐠 Live Animals: £12.00 (temperature-controlled)")
    print(f"   - Live shrimp, snails, fish")
    print(f"   - Special handling required")
    print(f"")
    print(f"📦 Non-Live Items: £6.00 (standard)")
    print(f"   - Plants, food, equipment, decorations")
    print(f"   - Standard packaging")
    print(f"")
    print(f"🔄 Mixed Cart: £12.00")
    print(f"   - Live animal shipping cost applies")
    print(f"   - Ensures proper handling for all items")
    
    # Test results
    all_correct = (
        shipping1 == Decimal('12.00') and
        shipping2 == Decimal('6.00') and 
        shipping3 == Decimal('12.00') and
        shipping4 == Decimal('0.00')
    )
    
    print(f"\n🎯 Final Result:")
    if all_correct:
        print(f"✅ ALL SHIPPING COSTS CORRECT!")
        print(f"   Aquarium store shipping rules working perfectly")
    else:
        print(f"❌ Some shipping costs are incorrect")
        print(f"   Please check the cart.py shipping logic")
    
    return all_correct

def show_product_shipping_breakdown():
    """Show which products get which shipping cost"""
    print(f"\n📊 Product Shipping Breakdown:")
    print(f"=" * 35)
    
    live_products = []
    non_live_products = []
    
    for product in Product.objects.all().order_by('category__order', 'name'):
        if product.is_shrimp_product:
            live_products.append(product)
        else:
            non_live_products.append(product)
    
    print(f"\n🐠 LIVE ANIMALS (£12 shipping):")
    for product in live_products:
        print(f"   • {product.name} - {product.category.name}")
    
    print(f"\n📦 NON-LIVE ITEMS (£6 shipping):")
    for product in non_live_products:
        print(f"   • {product.name} - {product.category.name}")

if __name__ == '__main__':
    success = test_shipping_costs()
    show_product_shipping_breakdown()
    
    if success:
        print(f"\n🎉 Somerset Shrimp Shack shipping costs updated successfully!")
        print(f"   Ready for aquarium business operations")
    else:
        print(f"\n⚠️  Please check shipping cost configuration")
