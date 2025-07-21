"""
Django management command to diagnose and fix store issues
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from store.models import Order, OrderItem, Product, Category
from store.utils import send_order_notification_email, send_order_confirmation_email
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Diagnose and fix store issues: stock counting, notifications, stock management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-stock',
            action='store_true',
            help='Check stock deduction in recent orders'
        )
        parser.add_argument(
            '--check-emails',
            action='store_true',
            help='Check email notification system'
        )
        parser.add_argument(
            '--test-stock-management',
            action='store_true',
            help='Test stock management page data'
        )
        parser.add_argument(
            '--fix-issues',
            action='store_true',
            help='Attempt to fix identified issues'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('Somerset Shrimp Shack - Store Diagnostics'))
        self.stdout.write('=' * 60)
        
        if options['check_stock']:
            self._check_stock_deduction()
        
        if options['check_emails']:
            self._check_email_system()
            
        if options['test_stock_management']:
            self._test_stock_management()
            
        if options['fix_issues']:
            self._fix_common_issues()
        
        if not any([options['check_stock'], options['check_emails'], 
                   options['test_stock_management'], options['fix_issues']]):
            self._run_full_diagnostics()

    def _run_full_diagnostics(self):
        """Run all diagnostic checks"""
        self.stdout.write(self.style.HTTP_INFO('\n🔍 Running Full Store Diagnostics:'))
        self._check_stock_deduction()
        self._check_email_system()
        self._test_stock_management()

    def _check_stock_deduction(self):
        """Check if stock is being deducted properly from recent orders"""
        self.stdout.write(self.style.HTTP_INFO('\n📦 Stock Deduction Analysis:'))
        
        # Get recent paid orders
        recent_orders = Order.objects.filter(status='paid').order_by('-created_at')[:5]
        
        if not recent_orders.exists():
            self.stdout.write(self.style.WARNING('⚠️  No paid orders found to check'))
            return
        
        for order in recent_orders:
            self.stdout.write(f'\n📋 Order #{order.order_reference} (ID: {order.id}):')
            self.stdout.write(f'   Status: {order.status}')
            self.stdout.write(f'   Date: {order.created_at}')
            
            order_items = order.items.select_related('product').all()
            
            if not order_items.exists():
                self.stdout.write(self.style.ERROR('   ✗ No order items found - this is a problem!'))
                continue
            
            for item in order_items:
                self.stdout.write(f'   • {item.product.name}:')
                self.stdout.write(f'     - Quantity ordered: {item.quantity}')
                self.stdout.write(f'     - Current stock: {item.product.stock}')
                
                # Check if stock seems reasonable
                if item.product.stock < 0:
                    self.stdout.write(self.style.ERROR('     ✗ Negative stock - oversold!'))
                elif item.product.stock == 0 and item.quantity > 0:
                    self.stdout.write(self.style.WARNING('     ⚠️  Stock is zero - might be sold out'))
                else:
                    self.stdout.write(self.style.SUCCESS('     ✓ Stock looks reasonable'))

    def _check_email_system(self):
        """Check email notification system"""
        self.stdout.write(self.style.HTTP_INFO('\n📧 Email System Analysis:'))
        
        # Check email settings
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not configured')
        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'Not configured')
        
        self.stdout.write(f'Email Backend: {email_backend}')
        self.stdout.write(f'Default From Email: {default_from}')
        self.stdout.write(f'Admin Email: {admin_email}')
        
        # Check recent orders for email sending
        recent_orders = Order.objects.filter(status='paid').order_by('-created_at')[:3]
        
        if recent_orders.exists():
            self.stdout.write(f'\n📨 Testing email system with recent order:')
            test_order = recent_orders.first()
            
            try:
                # Test sending notification email
                result = send_order_notification_email(test_order)
                if result:
                    self.stdout.write(self.style.SUCCESS(f'✓ Order notification email test successful'))
                else:
                    self.stdout.write(self.style.ERROR(f'✗ Order notification email test failed'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Email test error: {str(e)}'))
        else:
            self.stdout.write(self.style.WARNING('⚠️  No paid orders to test email with'))

    def _test_stock_management(self):
        """Test stock management page data"""
        self.stdout.write(self.style.HTTP_INFO('\n🏪 Stock Management Analysis:'))
        
        # Test basic queries
        total_products = Product.objects.count()
        self.stdout.write(f'Total products: {total_products}')
        
        if total_products == 0:
            self.stdout.write(self.style.ERROR('✗ No products found!'))
            return
        
        # Test products with categories
        products_with_categories = Product.objects.select_related('category').count()
        self.stdout.write(f'Products with category data loaded: {products_with_categories}')
        
        # Test category filtering
        categories = Category.objects.all()
        self.stdout.write(f'Total categories: {categories.count()}')
        
        for category in categories[:5]:  # Test first 5 categories
            product_count = Product.objects.filter(category=category).count()
            self.stdout.write(f'   • {category.name}: {product_count} products')
            
            if product_count == 0:
                self.stdout.write(self.style.WARNING(f'     ⚠️  Category "{category.name}" has no products'))
        
        # Test stock status filtering
        low_stock = Product.objects.filter(stock__gt=0, stock__lte=5).count()
        out_of_stock = Product.objects.filter(stock=0).count()
        unavailable = Product.objects.filter(available=False).count()
        
        self.stdout.write(f'\nStock Status Summary:')
        self.stdout.write(f'   • Low stock (1-5 items): {low_stock}')
        self.stdout.write(f'   • Out of stock: {out_of_stock}')  
        self.stdout.write(f'   • Unavailable: {unavailable}')

    def _fix_common_issues(self):
        """Attempt to fix common issues"""
        self.stdout.write(self.style.HTTP_INFO('\n🔧 Attempting to Fix Common Issues:'))
        
        # Fix 1: Check for orders without order items
        orders_without_items = Order.objects.filter(items__isnull=True, status='paid')
        if orders_without_items.exists():
            self.stdout.write(self.style.WARNING(f'⚠️  Found {orders_without_items.count()} paid orders without items'))
            
        # Fix 2: Check for negative stock
        negative_stock = Product.objects.filter(stock__lt=0)
        if negative_stock.exists():
            self.stdout.write(self.style.ERROR(f'✗ Found {negative_stock.count()} products with negative stock'))
            for product in negative_stock:
                self.stdout.write(f'   • {product.name}: {product.stock}')
                
        # Fix 3: Check for products without categories
        no_category = Product.objects.filter(category__isnull=True)
        if no_category.exists():
            self.stdout.write(self.style.WARNING(f'⚠️  Found {no_category.count()} products without categories'))
            
        self.stdout.write(self.style.SUCCESS('\n✅ Diagnostic scan completed!'))
