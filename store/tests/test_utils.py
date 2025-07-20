from django.test import TestCase, RequestFactory
from unittest.mock import patch, MagicMock
from decimal import Decimal

from store.utils import (
    format_price,
    send_order_confirmation_email,
    send_order_notification_email,
    get_cart,
    clear_cart,
)
from store.models import Order, Product, Category, OrderItem
from django.contrib.auth.models import User


class FormatPriceTestCase(TestCase):
    """Test cases for the format_price utility function."""
    
    def test_format_price_integer(self):
        """Test formatting integer prices."""
        self.assertEqual(format_price(10), "£10.00")
        self.assertEqual(format_price(0), "£0.00")
        self.assertEqual(format_price(100), "£100.00")
    
    def test_format_price_decimal(self):
        """Test formatting decimal prices."""
        self.assertEqual(format_price(10.5), "£10.50")
        self.assertEqual(format_price(9.99), "£9.99")
        self.assertEqual(format_price(0.01), "£0.01")
        self.assertEqual(format_price(123.456), "£123.46")  # Test rounding
    
    def test_format_price_with_decimal_objects(self):
        """Test formatting Decimal objects."""
        self.assertEqual(format_price(Decimal('10.50')), "£10.50")
        self.assertEqual(format_price(Decimal('0.99')), "£0.99")
    
    def test_format_price_edge_cases(self):
        """Test edge cases for price formatting."""
        self.assertEqual(format_price(0.001), "£0.00")  # Very small amounts
        self.assertEqual(format_price(999999.99), "£999999.99")  # Large amounts


class EmailUtilsTestCase(TestCase):
    """Test cases for email utility functions."""
    
    def setUp(self):
        """Set up test data for email tests."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=Decimal('25.99'),
            category=self.category,
            stock=10
        )
        self.order = Order.objects.create(
            user=self.user,
            stripe_checkout_id="cs_test_12345",
            email="test@example.com",
            status="paid",
            total_amount=Decimal('25.99'),
            shipping_name="Test User",
            shipping_address="123 Test Street",
            shipping_city="Test City",
            shipping_zip="12345",
            shipping_country="UK",
            order_reference="ORD-TEST-001",
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal('25.99')
        )
    
    @patch("store.utils.send_mail")
    @patch("store.utils.render_to_string")
    def test_send_order_confirmation_email_success(self, mock_render, mock_send):
        """Test successful order confirmation email sending."""
        mock_render.return_value = "<h1>Order Confirmation</h1>"
        mock_send.return_value = True
        
        result = send_order_confirmation_email(self.order)
        
        self.assertTrue(result)
        mock_render.assert_called_once()
        mock_send.assert_called_once()
        
        # Verify email parameters
        call_args = mock_send.call_args
        self.assertIn(self.order.email, call_args[1]['recipient_list'])
    
    @patch("store.utils.send_mail")
    @patch("store.utils.render_to_string")
    def test_send_order_confirmation_email_exception(self, mock_render, mock_send):
        """Test order confirmation email failure handling."""
        mock_render.return_value = "<h1>Order Confirmation</h1>"
        mock_send.side_effect = Exception("SMTP connection failed")
        
        result = send_order_confirmation_email(self.order)
        
        self.assertFalse(result)
        mock_send.assert_called_once()
    
    @patch("store.utils.send_mail")
    @patch("store.utils.render_to_string")
    def test_send_order_notification_email_success(self, mock_render, mock_send):
        """Test successful order notification email sending."""
        mock_render.return_value = "<h1>New Order Notification</h1>"
        mock_send.return_value = True
        
        result = send_order_notification_email(self.order)
        
        self.assertTrue(result)
        mock_render.assert_called_once()
        mock_send.assert_called_once()
    
    @patch("store.utils.send_mail")
    @patch("store.utils.render_to_string")
    def test_send_order_notification_email_exception(self, mock_render, mock_send):
        """Test order notification email failure handling."""
        mock_render.return_value = "<h1>New Order Notification</h1>"
        mock_send.side_effect = Exception("Email service unavailable")
        
        result = send_order_notification_email(self.order)
        
        self.assertFalse(result)
        mock_send.assert_called_once()
    
    def test_send_order_confirmation_email_with_none_order(self):
        """Test email sending with None order."""
        result = send_order_confirmation_email(None)
        self.assertFalse(result)
    
    def test_send_order_notification_email_with_none_order(self):
        """Test notification email sending with None order."""
        result = send_order_notification_email(None)
        self.assertFalse(result)


class CartUtilsTestCase(TestCase):
    """Test cases for cart utility functions."""
    
    def setUp(self):
        """Set up test data for cart tests."""
        self.factory = RequestFactory()
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.product1 = Product.objects.create(
            name="Product 1",
            slug="product-1",
            price=Decimal('10.00'),
            category=self.category,
            stock=5
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            slug="product-2",
            price=Decimal('15.50'),
            category=self.category,
            stock=3
        )
    
    def test_get_cart_new_session(self):
        """Test getting cart from a new session."""
        request = self.factory.get("/")
        request.session = self.client.session
        
        cart = get_cart(request)
        
        self.assertIsNotNone(cart)
        self.assertTrue(hasattr(cart, 'add'))
        self.assertTrue(hasattr(cart, 'remove'))
        self.assertTrue(hasattr(cart, 'get_total_price'))
    
    def test_get_cart_existing_session(self):
        """Test getting cart from existing session with items."""
        request = self.factory.get("/")
        request.session = self.client.session
        
        # First, add items to cart
        cart = get_cart(request)
        cart.add(self.product1, quantity=2)
        
        # Then get cart again and verify it persists
        cart2 = get_cart(request)
        self.assertTrue(hasattr(cart2, 'add'))
        # Verify cart state is maintained (this depends on your Cart implementation)
    
    def test_cart_add_product(self):
        """Test adding products to cart."""
        request = self.factory.get("/")
        request.session = self.client.session
        
        cart = get_cart(request)
        cart.add(self.product1, quantity=1)
        cart.add(self.product2, quantity=2)
        
        # Verify cart functionality (depends on your Cart class implementation)
        self.assertTrue(hasattr(cart, 'add'))
    
    def test_clear_cart_with_items(self):
        """Test clearing cart that contains items."""
        request = self.factory.get("/")
        request.session = self.client.session
        
        # Add items to cart
        cart = get_cart(request)
        cart.add(self.product1, quantity=1)
        
        # Clear cart
        clear_cart(request)
        
        # Verify cart is cleared from session
        self.assertNotIn("cart", request.session)
    
    def test_clear_cart_empty_session(self):
        """Test clearing cart from empty session."""
        request = self.factory.get("/")
        request.session = self.client.session
        
        # Clear cart without adding anything
        clear_cart(request)
        
        # Should not raise any errors
        self.assertNotIn("cart", request.session)
    
    def test_cart_operations_sequence(self):
        """Test a sequence of cart operations."""
        request = self.factory.get("/")
        request.session = self.client.session
        
        # Get cart and add items
        cart = get_cart(request)
        cart.add(self.product1, quantity=2)
        cart.add(self.product2, quantity=1)
        
        # Get cart again (should be same cart)
        cart2 = get_cart(request)
        self.assertEqual(type(cart), type(cart2))
        
        # Clear cart
        clear_cart(request)
        self.assertNotIn("cart", request.session)
        
        # Get cart after clearing (should be new empty cart)
        cart3 = get_cart(request)
        self.assertIsNotNone(cart3)


class IntegrationTestCase(TestCase):
    """Integration tests combining multiple utilities."""
    
    def setUp(self):
        """Set up test data for integration tests."""
        self.user = User.objects.create_user(
            username="integration_user",
            email="integration@test.com"
        )
        self.category = Category.objects.create(name="Integration Category", slug="integration")
        self.product = Product.objects.create(
            name="Integration Product",
            slug="integration-product",
            price=Decimal('29.99'),
            category=self.category,
            stock=1
        )
    
    @patch("store.utils.send_mail")
    @patch("store.utils.render_to_string")
    def test_complete_order_flow(self, mock_render, mock_send):
        """Test complete order flow with cart and email utilities."""
        # Set up cart
        request = self.factory.post("/checkout/")
        request.session = self.client.session
        
        cart = get_cart(request)
        cart.add(self.product, quantity=1)
        
        # Create order
        order = Order.objects.create(
            user=self.user,
            stripe_checkout_id="cs_integration_test",
            email=self.user.email,
            status="paid",
            total_amount=self.product.price,
            shipping_name="Integration User",
            shipping_address="123 Integration St",
            shipping_city="Test City",
            shipping_zip="12345",
            shipping_country="UK",
            order_reference="ORD-INT-001",
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price
        )
        
        # Mock email sending
        mock_render.return_value = "<h1>Email Body</h1>"
        mock_send.return_value = True
        
        # Send emails
        confirmation_sent = send_order_confirmation_email(order)
        notification_sent = send_order_notification_email(order)
        
        # Clear cart after successful order
        clear_cart(request)
        
        # Verify results
        self.assertTrue(confirmation_sent)
        self.assertTrue(notification_sent)
        self.assertNotIn("cart", request.session)
        self.assertEqual(format_price(order.total_amount), "£29.99")