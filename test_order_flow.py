#!/usr/bin/env python
"""
Test script to simulate a customer order and check stock deduction and email notifications
"""
import os
import django
import uuid

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Product, Order, OrderItem
from decimal import Decimal
import json
from django.contrib.auth.models import User

def create_test_order():
    """Create a test order to verify stock and email functionality"""
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='testcustomer',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'Customer'
        }
    )
    
    # Get some products to order
    king_prawns = Product.objects.get(slug='king-prawns-large')
    tiger_prawns = Product.objects.get(slug='tiger-prawns-medium')
    
    print(f"Before order:")
    print(f"King Prawns stock: {king_prawns.stock}")
    print(f"Tiger Prawns stock: {tiger_prawns.stock}")
    
    # Create order
    order = Order.objects.create(
        user=user,
        email=user.email,
        status='pending',
        total_amount=Decimal('0.00'),
        stripe_checkout_id=f'cs_test_{uuid.uuid4().hex[:12]}',
        shipping_name=f"{user.first_name} {user.last_name}",
        shipping_address="123 Test Street",
        shipping_city="Test City",
        shipping_zip="TE1 1ST",
        shipping_country="United Kingdom",
        shipping_phone="01234567890"
    )
    
    # Create order items
    item1 = OrderItem.objects.create(
        order=order,
        product=king_prawns,
        quantity=2,
        price=king_prawns.price
    )
    
    item2 = OrderItem.objects.create(
        order=order,
        product=tiger_prawns,
        quantity=3,
        price=tiger_prawns.price
    )
    
    # Calculate total
    order.total_amount = (item1.price * item1.quantity) + (item2.price * item2.quantity)
    order.save()
    
    print(f"\n✓ Created test order #{order.id}")
    print(f"Order total: £{order.total_amount}")
    print(f"Items:")
    print(f"  - {item1.quantity}x {item1.product.name} @ £{item1.price}")
    print(f"  - {item2.quantity}x {item2.product.name} @ £{item2.price}")
    
    return order

def simulate_payment_completion(order):
    """Simulate Stripe webhook for payment completion"""
    print(f"\n🔄 Simulating payment completion for order #{order.id}...")
    
    # Update order status to paid
    order.status = 'paid'
    order.save()
    
    # Manually trigger stock deduction (simulating what webhook should do)
    for item in order.items.all():
        old_stock = item.product.stock
        item.product.stock = max(0, item.product.stock - item.quantity)
        item.product.save()
        print(f"  Stock update: {item.product.name} {old_stock} → {item.product.stock}")
    
    print("✓ Order marked as paid and stock deducted")

def test_email_notification(order):
    """Test email notification system"""
    print(f"\n📧 Testing email notifications...")
    
    try:
        # Import the email notification functions
        from store.utils import send_order_confirmation_email, send_order_notification_email
        
        # Try to send order confirmation
        result1 = send_order_confirmation_email(order)
        if result1:
            print("✓ Order confirmation email sent successfully")
        else:
            print("❌ Order confirmation email failed")
            
        # Try to send admin notification
        result2 = send_order_notification_email(order)
        if result2:
            print("✓ Admin notification email sent successfully")
        else:
            print("❌ Admin notification email failed")
            
    except ImportError as e:
        print(f"⚠️  Email utility function not found: {e}")
    except Exception as e:
        print(f"❌ Email error: {str(e)}")

def main():
    print("Somerset Shrimp Shack - Order Testing")
    print("=" * 45)
    
    # Create test order
    order = create_test_order()
    
    # Simulate payment completion
    simulate_payment_completion(order)
    
    # Test email notifications
    test_email_notification(order)
    
    # Final status check
    print(f"\n📊 Final Status:")
    for item in order.items.all():
        product = Product.objects.get(id=item.product.id)  # Refresh from DB
        print(f"  {product.name}: {product.stock} in stock")
    
    print(f"\n✅ Test completed. Order #{order.id} created and processed.")

if __name__ == '__main__':
    main()
