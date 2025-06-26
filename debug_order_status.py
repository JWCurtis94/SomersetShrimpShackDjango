#!/usr/bin/env python
"""
Debug script to check order status update functionality
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Order

def debug_order_status():
    print("=== Order Status Debug ===")
    
    # Check if we have any orders
    orders = Order.objects.all()
    print(f"Total orders in database: {orders.count()}")
    
    if orders.count() > 0:
        first_order = orders.first()
        print(f"First order: {first_order.order_reference}")
        print(f"Current status: {first_order.status}")
        print(f"Status display: {first_order.get_status_display()}")
        
        # Check status choices
        print(f"Available status choices: {Order.STATUS_CHOICES}")
        print(f"Status choice values: {[choice[0] for choice in Order.STATUS_CHOICES]}")
        
        # Test status validation
        test_statuses = ['pending', 'paid', 'shipped', 'delivered', 'cancelled', 'invalid']
        for status in test_statuses:
            is_valid = status in [choice[0] for choice in Order.STATUS_CHOICES]
            print(f"Status '{status}' is valid: {is_valid}")
    
    else:
        print("No orders found in database")

if __name__ == "__main__":
    debug_order_status()
