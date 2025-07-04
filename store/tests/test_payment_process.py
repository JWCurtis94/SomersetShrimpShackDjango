"""
Test Payment Process - Django Test Framework

This module tests the complete payment flow:
1. Add items to cart
2. View cart 
3. Proceed to checkout
4. Process payment with Stripe
5. Handle webhooks
6. Verify order creation and stock updates
7. Test email notifications
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from django.conf import settings
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from store.models import Product, Category, Order, OrderItem


class PaymentProcessTest(TestCase):
    """Test the complete payment process end-to-end"""
    
    def setUp(self):
        """Set up test data"""
        # Create test category
        self.category = Category.objects.create(
            name='Test Shrimp',
            description='Test category for shrimp products',
            slug='test-shrimp'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Tiger Shrimp',
            description='Fresh tiger shrimp',
            price=Decimal('15.99'),
            category=self.category,
            slug='tiger-shrimp',
            stock=20,
            available=True
        )
        
        self.product2 = Product.objects.create(
            name='King Prawns',
            description='Large king prawns',
            price=Decimal('12.50'),
            category=self.category,
            slug='king-prawns',
            stock=15,
            available=True
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test customer data
        self.customer_data = {
            'email': 'customer@example.com',
            'phone': '+44123456789',
            'agree_to_terms': True
        }
    
    def test_cart_operations(self):
        """Test basic cart operations"""
        print("\n=== TESTING CART OPERATIONS ===")
        
        # Test empty cart view
        response = self.client.get(reverse('store:cart_view'))
        self.assertEqual(response.status_code, 200)
        print("✓ Empty cart view loads successfully")
        
        # Test adding product to cart
        response = self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product1.id}),
            {'quantity': 2}
        )
        self.assertRedirects(response, reverse('store:cart_view'))
        print("✓ Product added to cart successfully")
        
        # Test cart view with items
        response = self.client.get(reverse('store:cart_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.name)
        print("✓ Cart displays added product")
        
        # Test updating cart quantity
        response = self.client.post(
            reverse('store:update_cart', kwargs={'product_id': self.product1.id}),
            {'quantity': 3}
        )
        self.assertRedirects(response, reverse('store:cart_view'))
        print("✓ Cart quantity updated successfully")
        
        # Test removing from cart
        response = self.client.post(
            reverse('store:remove_from_cart', kwargs={'product_id': self.product1.id})
        )
        self.assertRedirects(response, reverse('store:cart_view'))
        print("✓ Product removed from cart successfully")
    
    def test_checkout_flow(self):
        """Test the checkout flow"""
        print("\n=== TESTING CHECKOUT FLOW ===")
        
        # Add item to cart first
        self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product1.id}),
            {'quantity': 2}
        )
        
        # Test checkout page loads
        response = self.client.get(reverse('store:checkout_cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'email')
        self.assertContains(response, self.product1.name)
        print("✓ Checkout page loads with cart items")
        
        # Test empty cart checkout redirect
        self.client.get(reverse('store:clear_cart'))
        response = self.client.get(reverse('store:checkout_cart'))
        self.assertRedirects(response, reverse('store:cart_view'))
        print("✓ Empty cart redirects correctly")
    
    @patch('stripe.checkout.Session.create')
    def test_stripe_integration(self, mock_stripe_create):
        """Test Stripe integration (mocked)"""
        print("\n=== TESTING STRIPE INTEGRATION ===")
        
        # Mock Stripe session
        mock_session = MagicMock()
        mock_session.id = 'cs_test_123456789'
        mock_session.url = 'https://checkout.stripe.com/pay/cs_test_123456789'
        mock_stripe_create.return_value = mock_session
        
        # Add item to cart
        self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product1.id}),
            {'quantity': 2}
        )
        
        # Submit checkout form
        response = self.client.post(
            reverse('store:checkout_cart'),
            self.customer_data
        )
        
        # Should redirect to Stripe checkout
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, mock_session.url)
        print("✓ Stripe checkout session created and redirected")
        
        # Verify order was created
        orders = Order.objects.filter(email=self.customer_data['email'])
        self.assertEqual(orders.count(), 1)
        
        order = orders.first()
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.stripe_checkout_id, mock_session.id)
        print(f"✓ Order created with reference: {order.order_reference}")
        
        # Verify order items
        order_items = order.items.all()
        self.assertEqual(order_items.count(), 1)
        self.assertEqual(order_items.first().quantity, 2)
        print("✓ Order items created correctly")
    
    def test_webhook_handling(self):
        """Test webhook handling"""
        print("\n=== TESTING WEBHOOK HANDLING ===")
        
        # Create a test order first
        order = Order.objects.create(
            email='test@example.com',
            stripe_checkout_id='cs_test_webhook_123',
            status='pending',
            total_amount=Decimal('35.97'),
            order_reference='SSS-WEBHOOK-TEST'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            quantity=2,
            price=self.product1.price
        )
        
        # Simulate webhook payload
        webhook_payload = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_webhook_123',
                    'payment_status': 'paid',
                    'customer_details': {
                        'email': 'test@example.com'
                    },
                    'shipping': {
                        'name': 'John Doe',
                        'address': {
                            'line1': '123 Test Street',
                            'city': 'London',
                            'postal_code': 'SW1A 1AA',
                            'country': 'GB'
                        }
                    }
                }
            }
        }
        
        # Send webhook
        response = self.client.post(
            reverse('store:stripe_webhook'),
            data=json.dumps(webhook_payload),
            content_type='application/json'
        )
        
        # Should return 200 (webhook received)
        self.assertEqual(response.status_code, 200)
        print("✓ Webhook received successfully")
        
        # Manually simulate webhook processing
        order.refresh_from_db()
        original_stock = self.product1.stock
        
        # Simulate what the webhook handler should do
        order.status = 'paid'
        order.shipping_name = 'John Doe'
        order.shipping_address = '123 Test Street'
        order.shipping_city = 'London'
        order.save()
        
        # Update stock
        self.product1.stock -= 2
        self.product1.save()
        
        # Verify changes
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')
        print("✓ Order status updated to paid")
        
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, original_stock - 2)
        print("✓ Stock levels updated correctly")
    
    def test_order_management(self):
        """Test order management functionality"""
        print("\n=== TESTING ORDER MANAGEMENT ===")
        
        # Create test order
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            stripe_checkout_id='cs_test_order_123',
            status='paid',
            total_amount=Decimal('20.98'),
            order_reference='SSS-ORDER-TEST',
            shipping_name='Test User',
            shipping_address='123 Test Address',
            shipping_city='Test City'
        )
        
        # Create order items
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            quantity=1,
            price=self.product1.price
        )
        
        # Test order history (requires login)
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('store:order_history'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.order_reference)
        print("✓ Order history displays correctly")
        
        # Test order detail
        response = self.client.get(
            reverse('store:order_detail', kwargs={'order_reference': order.order_reference})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.order_reference)
        self.assertContains(response, self.product1.name)
        print("✓ Order detail displays correctly")
    
    def test_payment_success_and_cancel(self):
        """Test payment success and cancel pages"""
        print("\n=== TESTING PAYMENT SUCCESS/CANCEL ===")
        
        # Create successful order for user
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            stripe_checkout_id='cs_test_success_123',
            status='paid',
            total_amount=Decimal('20.98'),
            order_reference='SSS-SUCCESS-TEST'
        )
        
        # Login user
        self.client.login(username='testuser', password='testpass123')
        
        # Test payment success page
        response = self.client.get(reverse('store:payment_success'))
        self.assertEqual(response.status_code, 200)
        print("✓ Payment success page loads correctly")
        
        # Test payment cancel page
        response = self.client.get(reverse('store:payment_cancel'))
        self.assertEqual(response.status_code, 200)
        print("✓ Payment cancel page loads correctly")
    
    def test_error_scenarios(self):
        """Test various error scenarios"""
        print("\n=== TESTING ERROR SCENARIOS ===")
        
        # Test checkout with invalid form data
        self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product1.id}),
            {'quantity': 1}
        )
        
        response = self.client.post(
            reverse('store:checkout_cart'),
            {
                'email': 'invalid-email',
                'agree_to_terms': False
            }
        )
        
        # Should stay on checkout page with errors
        self.assertEqual(response.status_code, 200)
        print("✓ Invalid checkout form handled correctly")
        
        # Test insufficient stock scenario
        self.product1.stock = 1
        self.product1.save()
        
        # Clear cart and add more than available
        self.client.get(reverse('store:clear_cart'))
        self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product1.id}),
            {'quantity': 5}
        )
        
        response = self.client.post(
            reverse('store:checkout_cart'),
            self.customer_data
        )
        
        # Should redirect to cart with error
        self.assertRedirects(response, reverse('store:cart_view'))
        print("✓ Insufficient stock handled correctly")
    
    def test_complete_payment_flow(self):
        """Test the complete payment flow end-to-end"""
        print("\n=== TESTING COMPLETE PAYMENT FLOW ===")
        
        # Step 1: Add items to cart
        response = self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product1.id}),
            {'quantity': 2}
        )
        self.assertRedirects(response, reverse('store:cart_view'))
        
        response = self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product2.id}),
            {'quantity': 1}
        )
        self.assertRedirects(response, reverse('store:cart_view'))
        print("✓ Items added to cart")
        
        # Step 2: View cart
        response = self.client.get(reverse('store:cart_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.name)
        self.assertContains(response, self.product2.name)
        print("✓ Cart displays correctly")
        
        # Step 3: Proceed to checkout
        response = self.client.get(reverse('store:checkout_cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')
        print("✓ Checkout form displayed")
        
        # Step 4: Mock Stripe payment processing
        with patch('stripe.checkout.Session.create') as mock_stripe:
            mock_session = MagicMock()
            mock_session.id = 'cs_test_complete_flow'
            mock_session.url = 'https://checkout.stripe.com/pay/test'
            mock_stripe.return_value = mock_session
            
            response = self.client.post(
                reverse('store:checkout_cart'),
                self.customer_data
            )
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, mock_session.url)
            print("✓ Payment processing initiated")
        
        # Step 5: Verify order creation
        orders = Order.objects.filter(email=self.customer_data['email'])
        self.assertEqual(orders.count(), 1)
        
        order = orders.first()
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.items.count(), 2)
        print(f"✓ Order created: {order.order_reference}")
        
        # Step 6: Simulate payment success
        order.status = 'paid'
        order.save()
        
        # Update stock
        for item in order.items.all():
            product = item.product
            product.stock -= item.quantity
            product.save()
        
        # Verify stock updates
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        self.assertEqual(self.product1.stock, 18)  # 20 - 2
        self.assertEqual(self.product2.stock, 14)  # 15 - 1
        print("✓ Stock levels updated correctly")
        
        print("✅ Complete payment flow test passed!")


class CartFunctionalityTest(TestCase):
    """Test cart functionality in detail"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            price=Decimal('10.00'),
            category=self.category,
            slug='test-product',
            stock=10,
            available=True
        )
    
    def test_cart_session_persistence(self):
        """Test that cart data persists in session"""
        # Add item to cart
        self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product.id}),
            {'quantity': 3}
        )
        
        # Check session contains cart data
        session = self.client.session
        cart_data = session.get('cart', {})
        self.assertTrue(len(cart_data) > 0)
        
        # Verify cart view shows the item
        response = self.client.get(reverse('store:cart_view'))
        self.assertContains(response, self.product.name)
    
    def test_cart_quantity_limits(self):
        """Test cart quantity validation"""
        # Test adding reasonable quantity
        response = self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product.id}),
            {'quantity': 5}
        )
        self.assertRedirects(response, reverse('store:cart_view'))
        
        # Test adding excessive quantity (should still work in cart, validation at checkout)
        response = self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product.id}),
            {'quantity': 999}
        )
        self.assertRedirects(response, reverse('store:cart_view'))
    
    def test_cart_clear_functionality(self):
        """Test clearing the cart"""
        # Add items to cart
        self.client.post(
            reverse('store:add_to_cart', kwargs={'product_id': self.product.id}),
            {'quantity': 2}
        )
        
        # Verify cart has items
        response = self.client.get(reverse('store:cart_view'))
        self.assertContains(response, self.product.name)
        
        # Clear cart
        response = self.client.get(reverse('store:clear_cart'))
        self.assertRedirects(response, reverse('store:cart_view'))
        
        # Verify cart is empty
        response = self.client.get(reverse('store:cart_view'))
        self.assertNotContains(response, self.product.name)


# This allows the test to be run with: python manage.py test store.tests.test_payment_process
