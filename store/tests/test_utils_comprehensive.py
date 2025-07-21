"""
Comprehensive tests for store.utils module
This file provides complete test coverage for utility functions
"""
from django.test import TestCase, override_settings
from django.core import mail
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
from decimal import Decimal

from store.models import Order, OrderItem, Product, Category
from store.utils import send_order_confirmation_email, send_order_notification_email


class EmailUtilsTest(TestCase):
    """Test email utility functions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='customer@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Test Category',
            description='Test description'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            description='Test product description',
            price=Decimal('19.99'),
            category=self.category,
            stock=10,
            available=True
        )
        
        self.order = Order.objects.create(
            user=self.user,
            email='customer@example.com',
            status='pending',
            total_amount=Decimal('25.98'),
            order_reference='TEST123',
            stripe_checkout_id='cs_test_123',
            shipping_name='John Doe',
            shipping_address='123 Test Street',
            shipping_city='Test City',
            shipping_state='Test State',
            shipping_zip='12345',
            shipping_country='United Kingdom'
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal('19.99')
        )
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@somersetshrimp.com'
    )
    def test_send_order_confirmation_email_success(self):
        """Test successful order confirmation email sending"""
        result = send_order_confirmation_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, f'Order Confirmation - #{self.order.order_reference}')
        self.assertEqual(sent_email.to, [self.order.email])
        self.assertEqual(sent_email.from_email, 'noreply@somersetshrimp.com')
        self.assertIn(self.order.order_reference, sent_email.body)
        self.assertIn(self.product.name, sent_email.body)
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='noreply@somersetshrimp.com',
        ADMIN_EMAIL='admin@somersetshrimp.com'
    )
    def test_send_order_notification_email_success(self):
        """Test successful order notification email sending"""
        result = send_order_notification_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, f'New Order Received - #{self.order.order_reference}')
        self.assertEqual(sent_email.to, ['admin@somersetshrimp.com'])
        self.assertEqual(sent_email.from_email, 'noreply@somersetshrimp.com')
        self.assertIn(self.order.order_reference, sent_email.body)
        self.assertIn(self.product.name, sent_email.body)
        self.assertIn(self.order.shipping_name, sent_email.body)
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_send_order_notification_email_default_admin(self):
        """Test order notification email uses default admin email when not configured"""
        result = send_order_notification_email(self.order)
        
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ['admin@somersetshrimp.com'])  # Default fallback
    
    @patch('store.utils.send_mail')
    def test_send_order_confirmation_email_failure(self, mock_send_mail):
        """Test order confirmation email sending failure handling"""
        # Make send_mail raise an exception
        mock_send_mail.side_effect = Exception('SMTP server error')
        
        result = send_order_confirmation_email(self.order)
        
        self.assertFalse(result)
        mock_send_mail.assert_called_once()
    
    @patch('store.utils.send_mail')
    def test_send_order_notification_email_failure(self, mock_send_mail):
        """Test order notification email sending failure handling"""
        # Make send_mail raise an exception
        mock_send_mail.side_effect = Exception('SMTP server error')
        
        result = send_order_notification_email(self.order)
        
        self.assertFalse(result)
        mock_send_mail.assert_called_once()
    
    @patch('store.utils.logger')
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_send_order_confirmation_email_logging_success(self, mock_logger):
        """Test successful email sending is logged"""
        send_order_confirmation_email(self.order)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn('Confirmation email sent', log_message)
        self.assertIn(self.order.email, log_message)
    
    @patch('store.utils.logger')
    @patch('store.utils.send_mail')
    def test_send_order_confirmation_email_logging_failure(self, mock_send_mail, mock_logger):
        """Test failed email sending is logged"""
        error_message = 'SMTP connection failed'
        mock_send_mail.side_effect = Exception(error_message)
        
        send_order_confirmation_email(self.order)
        
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        self.assertIn('Failed to send confirmation email', log_message)
        self.assertIn(str(self.order.id), log_message)
    
    @patch('store.utils.logger')
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_send_order_notification_email_logging_success(self, mock_logger):
        """Test successful notification email is logged"""
        send_order_notification_email(self.order)
        
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        self.assertIn('Order notification email sent', log_message)
        self.assertIn('admin', log_message.lower())
    
    @patch('store.utils.logger')
    @patch('store.utils.send_mail')
    def test_send_order_notification_email_logging_failure(self, mock_send_mail, mock_logger):
        """Test failed notification email is logged"""
        error_message = 'Template not found'
        mock_send_mail.side_effect = Exception(error_message)
        
        send_order_notification_email(self.order)
        
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        self.assertIn('Failed to send order notification email', log_message)
        self.assertIn(str(self.order.id), log_message)
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_email_context_includes_all_order_details(self):
        """Test that email context includes all necessary order information"""
        send_order_confirmation_email(self.order)
        
        sent_email = mail.outbox[0]
        
        # Check that all important order details are in the email body
        self.assertIn(self.order.order_reference, sent_email.body)
        self.assertIn(str(self.order.total_price), sent_email.body)
        self.assertIn(str(self.order.shipping_cost), sent_email.body)
        self.assertIn(self.order.shipping_name, sent_email.body)
        self.assertIn(self.order.shipping_address, sent_email.body)
        self.assertIn(self.order.shipping_city, sent_email.body)
        
        # Check product details are included
        self.assertIn(self.product.name, sent_email.body)
        self.assertIn(str(self.product.price), sent_email.body)
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_email_handles_missing_shipping_info(self):
        """Test email handling when shipping info is missing"""
        # Create order without shipping info
        order_no_shipping = Order.objects.create(
            user=self.user,
            email='customer@example.com',
            status='pending',
            total_amount=Decimal('19.99'),
            order_reference='TEST456',
            stripe_checkout_id='cs_test_456'
            # Note: no shipping info fields
        )
        
        # Should not raise an exception
        result = send_order_confirmation_email(order_no_shipping)
        self.assertTrue(result)
        
        # Email should still be sent
        self.assertEqual(len(mail.outbox), 1)
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_multiple_order_items_in_email(self):
        """Test email includes all order items"""
        # Add another product and order item
        product2 = Product.objects.create(
            name='Second Product',
            description='Second product description',
            price=Decimal('9.99'),
            category=self.category,
            stock=5,
            available=True
        )
        
        OrderItem.objects.create(
            order=self.order,
            product=product2,
            quantity=2,
            price=Decimal('9.99')
        )
        
        send_order_confirmation_email(self.order)
        
        sent_email = mail.outbox[0]
        
        # Both products should be mentioned in the email
        self.assertIn(self.product.name, sent_email.body)
        self.assertIn(product2.name, sent_email.body)
    
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
    )
    def test_html_and_plain_text_versions(self):
        """Test that both HTML and plain text versions are sent"""
        send_order_confirmation_email(self.order)
        
        sent_email = mail.outbox[0]
        
        # Check that both body and HTML alternative exist
        self.assertTrue(sent_email.body)  # Plain text version
        self.assertEqual(len(sent_email.alternatives), 1)  # HTML version
        self.assertEqual(sent_email.alternatives[0][1], 'text/html')
    
    def test_email_functions_return_boolean(self):
        """Test that email functions return boolean values"""
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            result1 = send_order_confirmation_email(self.order)
            result2 = send_order_notification_email(self.order)
            
            self.assertIsInstance(result1, bool)
            self.assertIsInstance(result2, bool)
            self.assertTrue(result1)
            self.assertTrue(result2)
        
        # Test failure case
        with patch('store.utils.send_mail', side_effect=Exception('Error')):
            result3 = send_order_confirmation_email(self.order)
            result4 = send_order_notification_email(self.order)
            
            self.assertIsInstance(result3, bool)
            self.assertIsInstance(result4, bool)
            self.assertFalse(result3)
            self.assertFalse(result4)
