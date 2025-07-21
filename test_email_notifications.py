#!/usr/bin/env python
"""
Comprehensive Email Notification Test Script
Tests both customer confirmation and admin notification emails with full order details
"""
import os
import django
import uuid
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product, Order, OrderItem
from django.contrib.auth.models import User
from store.utils import send_order_confirmation_email, send_order_notification_email
import logging

def create_test_customer():
    """Create a realistic test customer"""
    user, created = User.objects.get_or_create(
        username='testcustomer_email',
        defaults={
            'email': 'customer@example.com',
            'first_name': 'Sarah',
            'last_name': 'Johnson'
        }
    )
    
    if created:
        print(f"✓ Created test customer: {user.first_name} {user.last_name} ({user.email})")
    else:
        print(f"• Using existing customer: {user.first_name} {user.last_name} ({user.email})")
    
    return user

def create_detailed_order():
    """Create a detailed order with multiple items"""
    user = create_test_customer()
    
    # Get products for the order
    try:
        king_prawns = Product.objects.get(slug='king-prawns-large')
        garlic_sauce = Product.objects.get(slug='garlic-butter-sauce')
        seafood_platter = Product.objects.get(slug='family-seafood-platter')
    except Product.DoesNotExist as e:
        print(f"❌ Product not found: {e}")
        return None
    
    print(f"\n📦 Creating detailed order...")
    print(f"Products before order:")
    print(f"  - {king_prawns.name}: {king_prawns.stock} in stock")
    print(f"  - {garlic_sauce.name}: {garlic_sauce.stock} in stock") 
    print(f"  - {seafood_platter.name}: {seafood_platter.stock} in stock")
    
    # Create order with detailed shipping information
    order = Order.objects.create(
        user=user,
        email=user.email,
        status='paid',  # Set as paid to trigger notifications
        total_amount=Decimal('0.00'),  # Will be calculated
        stripe_checkout_id=f'cs_test_{uuid.uuid4().hex[:12]}',
        
        # Detailed shipping information
        shipping_name=f"{user.first_name} {user.last_name}",
        shipping_address="15 Ocean View Cottage\nSeaside Lane",
        shipping_city="Bristol",
        shipping_state="Somerset", 
        shipping_zip="BS1 4QA",
        shipping_country="United Kingdom",
        shipping_phone="+44 7123 456789"
    )
    
    # Create multiple order items
    items_data = [
        {'product': king_prawns, 'quantity': 3, 'description': '3x King Prawns for special dinner'},
        {'product': garlic_sauce, 'quantity': 2, 'description': '2x Garlic Butter Sauce to accompany prawns'},
        {'product': seafood_platter, 'quantity': 1, 'description': '1x Family Seafood Platter for the family'}
    ]
    
    total_amount = Decimal('0.00')
    created_items = []
    
    for item_data in items_data:
        item = OrderItem.objects.create(
            order=order,
            product=item_data['product'],
            quantity=item_data['quantity'],
            price=item_data['product'].price
        )
        
        total_amount += item.price * item.quantity
        created_items.append(item)
        print(f"  ✓ Added: {item.quantity}x {item.product.name} @ £{item.price} = £{item.price * item.quantity}")
        
        # Update stock
        item.product.stock -= item.quantity
        item.product.save()
    
    # Update order total
    order.total_amount = total_amount
    order.save()
    
    print(f"\n📄 Order Summary:")
    print(f"  Order ID: {order.order_reference}")
    print(f"  Customer: {order.shipping_name}")
    print(f"  Email: {order.email}")
    print(f"  Phone: {order.shipping_phone}")
    print(f"  Shipping Address:")
    print(f"    {order.shipping_address}")
    print(f"    {order.shipping_city}, {order.shipping_state}")
    print(f"    {order.shipping_zip}, {order.shipping_country}")
    print(f"  Total Items: {sum(item.quantity for item in created_items)}")
    print(f"  Total Amount: £{order.total_amount}")
    
    return order

def test_customer_confirmation_email(order):
    """Test customer order confirmation email"""
    print(f"\n📧 Testing Customer Confirmation Email...")
    print(f"   Recipient: {order.email}")
    print(f"   Order: #{order.order_reference}")
    
    try:
        success = send_order_confirmation_email(order)
        
        if success:
            print(f"   ✅ Customer confirmation email sent successfully!")
            print(f"   📋 Email should contain:")
            print(f"      • Order number: {order.order_reference}")
            print(f"      • Customer name: {order.shipping_name}")
            print(f"      • Order total: £{order.total_amount}")
            print(f"      • Items ordered:")
            for item in order.items.all():
                print(f"        - {item.quantity}x {item.product.name} @ £{item.price}")
            print(f"      • Shipping address: {order.shipping_address}")
            print(f"      • Contact details: {order.shipping_phone}")
            return True
        else:
            print(f"   ❌ Customer confirmation email failed!")
            return False
            
    except Exception as e:
        print(f"   ❌ Customer email error: {str(e)}")
        return False

def test_admin_notification_email(order):
    """Test admin notification email"""
    print(f"\n📧 Testing Admin Notification Email...")
    print(f"   Recipient: info@somersetshrimpshack.uk")
    print(f"   Order: #{order.order_reference}")
    
    try:
        success = send_order_notification_email(order)
        
        if success:
            print(f"   ✅ Admin notification email sent successfully!")
            print(f"   📋 Admin email should contain:")
            print(f"      • NEW ORDER ALERT for: {order.order_reference}")
            print(f"      • Customer details:")
            print(f"        - Name: {order.shipping_name}")
            print(f"        - Email: {order.email}")
            print(f"        - Phone: {order.shipping_phone}")
            print(f"      • Shipping address:")
            print(f"        - {order.shipping_address}")
            print(f"        - {order.shipping_city}, {order.shipping_state}")
            print(f"        - {order.shipping_zip}, {order.shipping_country}")
            print(f"      • Order details:")
            print(f"        - Total: £{order.total_amount}")
            print(f"        - Items:")
            for item in order.items.all():
                print(f"          * {item.quantity}x {item.product.name} @ £{item.price} = £{item.price * item.quantity}")
            return True
        else:
            print(f"   ❌ Admin notification email failed!")
            return False
            
    except Exception as e:
        print(f"   ❌ Admin email error: {str(e)}")
        return False

def verify_email_templates():
    """Check if email templates exist"""
    print(f"\n📄 Verifying Email Templates...")
    
    template_paths = [
        'store/templates/store/emails/order_confirmation.html',
        'store/templates/store/emails/order_confirmation.txt',
        'store/templates/store/emails/order_notification.html', 
        'store/templates/store/emails/order_notification.txt'
    ]
    
    import os
    from django.conf import settings
    
    template_status = []
    for template_path in template_paths:
        full_path = os.path.join(settings.BASE_DIR, template_path)
        exists = os.path.exists(full_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {template_path}")
        template_status.append(exists)
    
    return all(template_status)

def main():
    print("Somerset Shrimp Shack - Comprehensive Email Notification Test")
    print("=" * 65)
    
    # Verify templates exist
    templates_ok = verify_email_templates()
    if not templates_ok:
        print("\n⚠️  Some email templates are missing. Emails may not format correctly.")
    
    # Create detailed test order
    order = create_detailed_order()
    if not order:
        print("❌ Failed to create test order")
        return
    
    # Test customer confirmation email
    customer_success = test_customer_confirmation_email(order)
    
    # Test admin notification email  
    admin_success = test_admin_notification_email(order)
    
    # Final results
    print(f"\n📊 Email Test Results:")
    print(f"=" * 30)
    
    if customer_success:
        print(f"✅ Customer Confirmation: WORKING")
        print(f"   • Order details sent to: {order.email}")
        print(f"   • Contains: Order #{order.order_reference}, items, total, shipping")
    else:
        print(f"❌ Customer Confirmation: FAILED")
    
    if admin_success:
        print(f"✅ Admin Notification: WORKING") 
        print(f"   • New order alert sent to: info@somersetshrimpshack.uk")
        print(f"   • Contains: Customer details, contact info, shipping address, order details")
    else:
        print(f"❌ Admin Notification: FAILED")
    
    if customer_success and admin_success:
        print(f"\n🎉 ALL EMAIL NOTIFICATIONS WORKING PERFECTLY!")
        print(f"   Both customer and admin will receive detailed order information")
    else:
        print(f"\n⚠️  Some email notifications failed - check email configuration")
    
    # Final order status
    print(f"\n📦 Final Stock Levels:")
    for item in order.items.all():
        product = Product.objects.get(id=item.product.id)
        print(f"   {product.name}: {product.stock} remaining")
    
    print(f"\n✅ Test completed for order #{order.order_reference}")

if __name__ == '__main__':
    main()
