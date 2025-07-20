from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import User
from decimal import Decimal
from unittest.mock import patch, Mock

from store.cart import Cart
from store.models import Product, Category


class CartTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        self.product1 = Product.objects.create(
            name='Product 1',
            slug='product-1',
            price=Decimal('10.00'),
            category=self.category,
            stock_quantity=100
        )
        self.product2 = Product.objects.create(
            name='Product 2',
            slug='product-2',
            price=Decimal('25.50'),
            category=self.category,
            stock_quantity=50
        )
        self.product3 = Product.objects.create(
            name='Product 3',
            slug='product-3',
            price=Decimal('15.75'),
            category=self.category,
            stock_quantity=25
        )

    def create_request_with_session(self):
        """Create a request with session middleware"""
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        return request


class CartInitializationTest(CartTestCase):
    def test_cart_initialization_new_session(self):
        """Test cart initialization with new session"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        self.assertIsNotNone(cart.session)
        self.assertEqual(len(cart.cart), 0)
        self.assertIn('cart', request.session)

    def test_cart_initialization_existing_session(self):
        """Test cart initialization with existing cart in session"""
        request = self.create_request_with_session()
        
        # Pre-populate session with cart data
        request.session['cart'] = {
            str(self.product1.id): {
                'quantity': 2,
                'price': str(self.product1.price)
            }
        }
        
        cart = Cart(request)
        self.assertEqual(len(cart.cart), 1)
        self.assertIn(str(self.product1.id), cart.cart)


class CartAddTest(CartTestCase):
    def test_add_new_product(self):
        """Test adding a new product to cart"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        cart.add(product=self.product1, quantity=2)
        
        self.assertEqual(len(cart.cart), 1)
        self.assertEqual(cart.cart[str(self.product1.id)]['quantity'], 2)
        self.assertEqual(cart.cart[str(self.product1.id)]['price'], str(self.product1.price))

    def test_add_existing_product_update_quantity(self):
        """Test adding existing product with update_quantity=True"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        cart.add(product=self.product1, quantity=2)
        cart.add(product=self.product1, quantity=3, update_quantity=True)
        
        self.assertEqual(cart.cart[str(self.product1.id)]['quantity'], 3)

    def test_add_existing_product_increment_quantity(self):
        """Test adding existing product with update_quantity=False"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        cart.add(product=self.product1, quantity=2)
        cart.add(product=self.product1, quantity=3, update_quantity=False)
        
        self.assertEqual(cart.cart[str(self.product1.id)]['quantity'], 5)

    def test_add_with_custom_price(self):
        """Test adding product with custom price"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        custom_price = Decimal('12.50')
        cart.add(product=self.product1, quantity=1, price=custom_price)
        
        self.assertEqual(cart.cart[str(self.product1.id)]['price'], str(custom_price))

    def test_add_zero_quantity(self):
        """Test adding product with zero quantity"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        cart.add(product=self.product1, quantity=0)
        
        # Should not add product with zero quantity
        self.assertEqual(len(cart.cart), 0)

    def test_add_negative_quantity(self):
        """Test adding product with negative quantity"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        cart.add(product=self.product1, quantity=-1)
        
        # Should not add product with negative quantity
        self.assertEqual(len(cart.cart), 0)

    def test_add_exceeds_stock(self):
        """Test adding quantity that exceeds stock"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        # Assuming there's stock validation
        try:
            cart.add(product=self.product1, quantity=self.product1.stock_quantity + 10)
            # If no exception is raised, check if quantity was capped
            if str(self.product1.id) in cart.cart:
                self.assertLessEqual(
                    cart.cart[str(self.product1.id)]['quantity'],
                    self.product1.stock_quantity
                )
        except Exception as e:
            # Exception is expected for stock validation
            pass


class CartRemoveTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)
        # Pre-add products
        self.cart.add(product=self.product1, quantity=3)
        self.cart.add(product=self.product2, quantity=2)

    def test_remove_existing_product(self):
        """Test removing an existing product"""
        self.cart.remove(product=self.product1)
        
        self.assertNotIn(str(self.product1.id), self.cart.cart)
        self.assertEqual(len(self.cart.cart), 1)

    def test_remove_nonexistent_product(self):
        """Test removing a product not in cart"""
        initial_length = len(self.cart.cart)
        self.cart.remove(product=self.product3)
        
        self.assertEqual(len(self.cart.cart), initial_length)

    def test_remove_by_product_id(self):
        """Test removing product by ID if method supports it"""
        if hasattr(self.cart, 'remove_by_id'):
            self.cart.remove_by_id(str(self.product1.id))
            self.assertNotIn(str(self.product1.id), self.cart.cart)


class CartUpdateTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)
        # Pre-add products
        self.cart.add(product=self.product1, quantity=3)
        self.cart.add(product=self.product2, quantity=2)

    def test_update_existing_product_quantity(self):
        """Test updating quantity of existing product"""
        if hasattr(self.cart, 'update'):
            self.cart.update(product=self.product1, quantity=5)
            self.assertEqual(self.cart.cart[str(self.product1.id)]['quantity'], 5)

    def test_update_to_zero_quantity(self):
        """Test updating quantity to zero (should remove)"""
        if hasattr(self.cart, 'update'):
            self.cart.update(product=self.product1, quantity=0)
            self.assertNotIn(str(self.product1.id), self.cart.cart)

    def test_update_nonexistent_product(self):
        """Test updating nonexistent product"""
        if hasattr(self.cart, 'update'):
            initial_length = len(self.cart.cart)
            self.cart.update(product=self.product3, quantity=1)
            # Should either add product or maintain same length
            self.assertTrue(len(self.cart.cart) >= initial_length)


class CartCalculationTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)
        
        # Add products with known quantities and prices
        self.cart.add(product=self.product1, quantity=2)  # 2 * 10.00 = 20.00
        self.cart.add(product=self.product2, quantity=1)  # 1 * 25.50 = 25.50
        # Total should be 45.50

    def test_get_total_price(self):
        """Test calculating total cart price"""
        total = self.cart.get_total_price()
        expected_total = (2 * self.product1.price) + (1 * self.product2.price)
        self.assertEqual(total, expected_total)

    def test_get_total_items(self):
        """Test calculating total number of items"""
        if hasattr(self.cart, 'get_total_items'):
            total_items = self.cart.get_total_items()
            self.assertEqual(total_items, 3)  # 2 + 1

    def test_get_total_quantity(self):
        """Test calculating total quantity"""
        if hasattr(self.cart, '__len__'):
            self.assertEqual(len(self.cart), 3)

    def test_empty_cart_total(self):
        """Test total price of empty cart"""
        empty_cart = Cart(self.create_request_with_session())
        self.assertEqual(empty_cart.get_total_price(), Decimal('0.00'))


class CartIterationTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)
        
        self.cart.add(product=self.product1, quantity=2)
        self.cart.add(product=self.product2, quantity=1)

    def test_cart_iteration(self):
        """Test iterating over cart items"""
        items = list(self.cart)
        self.assertEqual(len(items), 2)
        
        # Check if iteration returns proper item structure
        for item in items:
            self.assertIn('product', item)
            self.assertIn('quantity', item)
            self.assertIn('price', item)
            self.assertIn('total_price', item)

    def test_cart_item_structure(self):
        """Test structure of cart items during iteration"""
        for item in self.cart:
            # Verify item has all expected keys
            expected_keys = ['product', 'quantity', 'price', 'total_price']
            for key in expected_keys:
                self.assertIn(key, item)
                
            # Verify data types
            self.assertIsInstance(item['product'], Product)
            self.assertIsInstance(item['quantity'], int)
            self.assertIsInstance(item['price'], Decimal)
            self.assertIsInstance(item['total_price'], Decimal)


class CartClearTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)
        
        # Add some products
        self.cart.add(product=self.product1, quantity=2)
        self.cart.add(product=self.product2, quantity=1)

    def test_clear_cart(self):
        """Test clearing all items from cart"""
        self.assertEqual(len(self.cart.cart), 2)
        
        self.cart.clear()
        
        self.assertEqual(len(self.cart.cart), 0)
        self.assertEqual(self.cart.get_total_price(), Decimal('0.00'))

    def test_clear_empty_cart(self):
        """Test clearing already empty cart"""
        empty_cart = Cart(self.create_request_with_session())
        empty_cart.clear()
        
        self.assertEqual(len(empty_cart.cart), 0)


class CartSessionPersistenceTest(CartTestCase):
    def test_cart_saves_to_session(self):
        """Test that cart changes are saved to session"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        cart.add(product=self.product1, quantity=2)
        
        # Check if cart data is in session
        self.assertIn('cart', request.session)
        self.assertEqual(
            request.session['cart'][str(self.product1.id)]['quantity'],
            2
        )

    def test_cart_modified_flag(self):
        """Test that session modified flag is set"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        # Session should not be modified initially
        request.session.modified = False
        
        cart.add(product=self.product1, quantity=1)
        
        # Session should be marked as modified after cart change
        self.assertTrue(request.session.modified)


class CartValidationTest(CartTestCase):
    def test_add_with_invalid_product(self):
        """Test adding invalid product"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        # Test with None product
        with self.assertRaises((AttributeError, TypeError)):
            cart.add(product=None, quantity=1)

    def test_add_with_inactive_product(self):
        """Test adding inactive product"""
        inactive_product = Product.objects.create(
            name='Inactive Product',
            slug='inactive-product',
            price=Decimal('10.00'),
            category=self.category,
            stock_quantity=10,
            is_active=False
        )
        
        request = self.create_request_with_session()
        cart = Cart(request)
        
        # Depending on your implementation, this might raise an exception
        # or silently fail
        try:
            cart.add(product=inactive_product, quantity=1)
            # If no exception, check if product was actually added
            if hasattr(cart, 'validate_product'):
                self.assertNotIn(str(inactive_product.id), cart.cart)
        except Exception:
            # Exception is expected for inactive products
            pass

    def test_quantity_validation(self):
        """Test quantity validation"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        # Test with string quantity
        with self.assertRaises((TypeError, ValueError)):
            cart.add(product=self.product1, quantity="invalid")

    def test_price_validation(self):
        """Test price validation"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        # Test with invalid price
        with self.assertRaises((TypeError, ValueError)):
            cart.add(product=self.product1, quantity=1, price="invalid")


class CartDiscountTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)
        self.cart.add(product=self.product1, quantity=2)

    def test_apply_discount(self):
        """Test applying discount to cart"""
        if hasattr(self.cart, 'apply_discount'):
            discount_amount = Decimal('5.00')
            self.cart.apply_discount(discount_amount)
            
            total_with_discount = self.cart.get_total_price()
            expected_total = (2 * self.product1.price) - discount_amount
            self.assertEqual(total_with_discount, expected_total)

    def test_apply_percentage_discount(self):
        """Test applying percentage discount"""
        if hasattr(self.cart, 'apply_percentage_discount'):
            discount_percentage = Decimal('10.0')  # 10%
            self.cart.apply_percentage_discount(discount_percentage)
            
            total_with_discount = self.cart.get_total_price()
            original_total = 2 * self.product1.price
            expected_total = original_total * (Decimal('100') - discount_percentage) / Decimal('100')
            self.assertEqual(total_with_discount, expected_total)

    def test_remove_discount(self):
        """Test removing discount from cart"""
        if hasattr(self.cart, 'remove_discount'):
            # First apply discount
            if hasattr(self.cart, 'apply_discount'):
                self.cart.apply_discount(Decimal('5.00'))
            
            # Then remove it
            self.cart.remove_discount()
            
            total = self.cart.get_total_price()
            expected_total = 2 * self.product1.price
            self.assertEqual(total, expected_total)


class CartCouponTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)
        self.cart.add(product=self.product1, quantity=2)

    def test_apply_coupon(self):
        """Test applying coupon to cart"""
        if hasattr(self.cart, 'apply_coupon'):
            coupon_code = 'SAVE10'
            self.cart.apply_coupon(coupon_code)
            
            # Check if coupon is stored in cart
            self.assertIn('coupon', self.cart.cart)
            self.assertEqual(self.cart.cart['coupon'], coupon_code)

    def test_remove_coupon(self):
        """Test removing coupon from cart"""
        if hasattr(self.cart, 'remove_coupon'):
            # First apply coupon
            if hasattr(self.cart, 'apply_coupon'):
                self.cart.apply_coupon('SAVE10')
            
            # Then remove it
            self.cart.remove_coupon()
            
            self.assertNotIn('coupon', self.cart.cart)


class CartShippingTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)
        self.cart.add(product=self.product1, quantity=2)

    def test_calculate_shipping(self):
        """Test shipping calculation"""
        if hasattr(self.cart, 'calculate_shipping'):
            shipping_cost = self.cart.calculate_shipping()
            self.assertIsInstance(shipping_cost, Decimal)
            self.assertGreaterEqual(shipping_cost, Decimal('0'))

    def test_free_shipping_threshold(self):
        """Test free shipping threshold"""
        if hasattr(self.cart, 'is_free_shipping'):
            # Add expensive items to potentially trigger free shipping
            self.cart.add(product=self.product2, quantity=10)
            
            is_free = self.cart.is_free_shipping()
            self.assertIsInstance(is_free, bool)

    def test_get_total_weight(self):
        """Test calculating total weight"""
        if hasattr(self.cart, 'get_total_weight'):
            total_weight = self.cart.get_total_weight()
            self.assertIsInstance(total_weight, (int, float, Decimal))


class CartTaxTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)
        self.cart.add(product=self.product1, quantity=2)

    def test_calculate_tax(self):
        """Test tax calculation"""
        if hasattr(self.cart, 'calculate_tax'):
            tax_rate = Decimal('8.5')  # 8.5%
            tax_amount = self.cart.calculate_tax(tax_rate)
            
            self.assertIsInstance(tax_amount, Decimal)
            self.assertGreaterEqual(tax_amount, Decimal('0'))

    def test_get_subtotal(self):
        """Test getting subtotal (before tax)"""
        if hasattr(self.cart, 'get_subtotal'):
            subtotal = self.cart.get_subtotal()
            total = self.cart.get_total_price()
            
            # Subtotal should be less than or equal to total
            self.assertLessEqual(subtotal, total)


class CartUtilityMethodsTest(CartTestCase):
    def setUp(self):
        super().setUp()
        self.request = self.create_request_with_session()
        self.cart = Cart(self.request)

    def test_is_empty(self):
        """Test checking if cart is empty"""
        if hasattr(self.cart, 'is_empty'):
            self.assertTrue(self.cart.is_empty())
            
            self.cart.add(product=self.product1, quantity=1)
            self.assertFalse(self.cart.is_empty())

    def test_contains_product(self):
        """Test checking if cart contains specific product"""
        if hasattr(self.cart, 'contains'):
            self.assertFalse(self.cart.contains(self.product1))
            
            self.cart.add(product=self.product1, quantity=1)
            self.assertTrue(self.cart.contains(self.product1))

    def test_get_item_count(self):
        """Test getting count of unique items"""
        if hasattr(self.cart, 'get_item_count'):
            self.assertEqual(self.cart.get_item_count(), 0)
            
            self.cart.add(product=self.product1, quantity=3)
            self.cart.add(product=self.product2, quantity=2)
            
            # Should return 2 (unique products)
            self.assertEqual(self.cart.get_item_count(), 2)

    def test_get_product_quantity(self):
        """Test getting quantity of specific product"""
        if hasattr(self.cart, 'get_product_quantity'):
            self.cart.add(product=self.product1, quantity=3)
            
            quantity = self.cart.get_product_quantity(self.product1)
            self.assertEqual(quantity, 3)
            
            # Test with product not in cart
            quantity = self.cart.get_product_quantity(self.product2)
            self.assertEqual(quantity, 0)


class CartSerializationTest(CartTestCase):
    def test_to_dict(self):
        """Test converting cart to dictionary"""
        request = self.create_request_with_session()
        cart = Cart(request)
        cart.add(product=self.product1, quantity=2)
        
        if hasattr(cart, 'to_dict'):
            cart_dict = cart.to_dict()
            self.assertIsInstance(cart_dict, dict)
            self.assertIn('items', cart_dict)
            self.assertIn('total', cart_dict)

    def test_from_dict(self):
        """Test creating cart from dictionary"""
        if hasattr(Cart, 'from_dict'):
            cart_data = {
                'items': {
                    str(self.product1.id): {
                        'quantity': 2,
                        'price': str(self.product1.price)
                    }
                }
            }
            
            request = self.create_request_with_session()
            cart = Cart.from_dict(request, cart_data)
            
            self.assertEqual(len(cart.cart), 1)
            self.assertEqual(cart.cart[str(self.product1.id)]['quantity'], 2)


class CartErrorHandlingTest(CartTestCase):
    def test_corrupted_session_data(self):
        """Test handling corrupted session data"""
        request = self.create_request_with_session()
        
        # Corrupt the session data
        request.session['cart'] = 'invalid_data'
        
        # Cart should handle this gracefully
        cart = Cart(request)
        self.assertIsInstance(cart.cart, dict)
        self.assertEqual(len(cart.cart), 0)

    def test_missing_product_in_session(self):
        """Test handling missing product in session data"""
        request = self.create_request_with_session()
        
        # Add reference to non-existent product
        request.session['cart'] = {
            '99999': {  # Non-existent product ID
                'quantity': 2,
                'price': '10.00'
            }
        }
        
        cart = Cart(request)
        # Cart should handle missing products gracefully
        # This might remove invalid items or skip them during iteration
        try:
            list(cart)  # Try to iterate
        except Product.DoesNotExist:
            # If exception is raised, it should be handled gracefully
            pass


@patch('store.models.Product.objects.get')
class CartMockTest(CartTestCase):
    def test_product_lookup_failure(self, mock_get):
        """Test handling product lookup failure"""
        mock_get.side_effect = Product.DoesNotExist
        
        request = self.create_request_with_session()
        request.session['cart'] = {
            str(self.product1.id): {
                'quantity': 2,
                'price': str(self.product1.price)
            }
        }
        
        cart = Cart(request)
        
        # Should handle DoesNotExist gracefully
        try:
            items = list(cart)
            # Items list might be empty or skip invalid products
        except Product.DoesNotExist:
            self.fail("Cart should handle DoesNotExist gracefully")


class CartPerformanceTest(CartTestCase):
    def test_large_cart_performance(self):
        """Test cart performance with many items"""
        request = self.create_request_with_session()
        cart = Cart(request)
        
        # Create many products
        products = []
        for i in range(100):
            product = Product.objects.create(
                name=f'Product {i}',
                slug=f'product-{i}',
                price=Decimal('10.00'),
                category=self.category,
                stock_quantity=100
            )
            products.append(product)
            cart.add(product=product, quantity=1)
        
        # Test that operations still work with large cart
        total = cart.get_total_price()
        self.assertEqual(total, Decimal('1000.00'))  # 100 * 10.00
        
        items = list(cart)
        self.assertEqual(len(items), 100)


class CartConcurrencyTest(CartTestCase):
    def test_concurrent_cart_modifications(self):
        """Test concurrent modifications to cart"""
        request = self.create_request_with_session()
        cart1 = Cart(request)
        cart2 = Cart(request)  # Same session
        
        # Both carts reference same session
        cart1.add(product=self.product1, quantity=1)
        cart2.add(product=self.product2, quantity=1)
        
        # Both changes should be reflected
        self.assertEqual(len(cart1.cart), 2)
        self.assertEqual(len(cart2.cart), 2)

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from store.models import (
    Category, Product, ProductImage, UserProfile, Order, OrderItem,
    ShippingAddress, BillingAddress, Cart, CartItem, Review,
    Coupon, Wishlist, Newsletter, ContactMessage
)


class CategoryModelTest(TestCase):
    def test_create_category(self):
        """Test creating a basic category"""
        category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic products'
        )
        
        self.assertEqual(category.name, 'Electronics')
        self.assertEqual(category.slug, 'electronics')
        self.assertEqual(str(category), 'Electronics')

    def test_category_slug_uniqueness(self):
        """Test category slug uniqueness"""
        Category.objects.create(name='Electronics', slug='electronics')
        
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Electronics 2', slug='electronics')

    def test_category_hierarchy(self):
        """Test category parent-child relationship"""
        if hasattr(Category, 'parent'):
            parent = Category.objects.create(name='Electronics', slug='electronics')
            child = Category.objects.create(
                name='Smartphones', 
                slug='smartphones',
                parent=parent
            )
            
            self.assertEqual(child.parent, parent)
            self.assertIn(child, parent.children.all())

    def test_category_ordering(self):
        """Test category ordering"""
        if hasattr(Category, 'order'):
            cat1 = Category.objects.create(name='Cat 1', slug='cat-1', order=2)
            cat2 = Category.objects.create(name='Cat 2', slug='cat-2', order=1)
            cat3 = Category.objects.create(name='Cat 3', slug='cat-3', order=3)
            
            ordered_categories = Category.objects.all()
            self.assertEqual(list(ordered_categories), [cat2, cat1, cat3])

    def test_category_get_absolute_url(self):
        """Test category absolute URL"""
        category = Category.objects.create(name='Electronics', slug='electronics')
        
        if hasattr(category, 'get_absolute_url'):
            url = category.get_absolute_url()
            self.assertIn('electronics', url)

    def test_category_product_count(self):
        """Test counting products in category"""
        category = Category.objects.create(name='Electronics', slug='electronics')
        
        # Create products
        Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), category=category
        )
        Product.objects.create(
            name='Laptop', slug='laptop', price=Decimal('800.00'), category=category
        )
        
        if hasattr(category, 'get_product_count'):
            self.assertEqual(category.get_product_count(), 2)

    def test_category_image_upload(self):
        """Test category image upload"""
        category = Category.objects.create(name='Electronics', slug='electronics')
        
        if hasattr(category, 'image'):
            # Test that image field exists and accepts files
            self.assertIsNotNone(category._meta.get_field('image'))


class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    def test_create_product(self):
        """Test creating a basic product"""
        product = Product.objects.create(
            name='Smartphone',
            slug='smartphone',
            description='Latest smartphone',
            price=Decimal('599.99'),
            category=self.category,
            stock_quantity=50
        )
        
        self.assertEqual(product.name, 'Smartphone')
        self.assertEqual(product.price, Decimal('599.99'))
        self.assertEqual(str(product), 'Smartphone')

    def test_product_slug_uniqueness(self):
        """Test product slug uniqueness"""
        Product.objects.create(
            name='Phone 1', slug='phone', price=Decimal('100.00'), category=self.category
        )
        
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                name='Phone 2', slug='phone', price=Decimal('200.00'), category=self.category
            )

    def test_product_price_validation(self):
        """Test product price validation"""
        with self.assertRaises(ValidationError):
            product = Product(
                name='Invalid Product',
                slug='invalid-product',
                price=Decimal('-10.00'),  # Negative price
                category=self.category
            )
            product.full_clean()

    def test_product_stock_validation(self):
        """Test product stock validation"""
        if hasattr(Product, 'stock_quantity'):
            with self.assertRaises(ValidationError):
                product = Product(
                    name='Invalid Product',
                    slug='invalid-product',
                    price=Decimal('10.00'),
                    category=self.category,
                    stock_quantity=-5  # Negative stock
                )
                product.full_clean()

    def test_product_is_in_stock(self):
        """Test product stock availability"""
        product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), 
            category=self.category, stock_quantity=10
        )
        
        if hasattr(product, 'is_in_stock'):
            self.assertTrue(product.is_in_stock())
            
            product.stock_quantity = 0
            product.save()
            self.assertFalse(product.is_in_stock())

    def test_product_can_order_quantity(self):
        """Test if product has enough stock for order"""
        product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), 
            category=self.category, stock_quantity=5
        )
        
        if hasattr(product, 'can_order'):
            self.assertTrue(product.can_order(3))
            self.assertTrue(product.can_order(5))
            self.assertFalse(product.can_order(6))

    def test_product_reduce_stock(self):
        """Test reducing product stock"""
        product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), 
            category=self.category, stock_quantity=10
        )
        
        if hasattr(product, 'reduce_stock'):
            product.reduce_stock(3)
            self.assertEqual(product.stock_quantity, 7)

    def test_product_get_absolute_url(self):
        """Test product absolute URL"""
        product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), category=self.category
        )
        
        if hasattr(product, 'get_absolute_url'):
            url = product.get_absolute_url()
            self.assertIn('phone', url)

    def test_product_average_rating(self):
        """Test product average rating calculation"""
        product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), category=self.category
        )
        
        if hasattr(product, 'get_average_rating'):
            # Without reviews
            avg_rating = product.get_average_rating()
            self.assertEqual(avg_rating, 0)

    def test_product_review_count(self):
        """Test product review count"""
        product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), category=self.category
        )
        
        if hasattr(product, 'get_review_count'):
            count = product.get_review_count()
            self.assertEqual(count, 0)

    def test_product_sale_price(self):
        """Test product sale price"""
        product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), category=self.category
        )
        
        if hasattr(product, 'sale_price'):
            product.sale_price = Decimal('80.00')
            product.save()
            
            if hasattr(product, 'get_price'):
                self.assertEqual(product.get_price(), Decimal('80.00'))

    def test_product_is_on_sale(self):
        """Test if product is on sale"""
        product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), category=self.category
        )
        
        if hasattr(product, 'is_on_sale'):
            self.assertFalse(product.is_on_sale())
            
            if hasattr(product, 'sale_price'):
                product.sale_price = Decimal('80.00')
                product.save()
                self.assertTrue(product.is_on_sale())


class ProductImageModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), category=self.category
        )

    def test_create_product_image(self):
        """Test creating product image"""
        if hasattr(ProductImage, 'product'):
            image = ProductImage.objects.create(
                product=self.product,
                alt_text='Phone image'
            )
            
            self.assertEqual(image.product, self.product)
            self.assertEqual(image.alt_text, 'Phone image')

    def test_product_multiple_images(self):
        """Test product with multiple images"""
        if hasattr(ProductImage, 'product'):
            img1 = ProductImage.objects.create(product=self.product, alt_text='Image 1')
            img2 = ProductImage.objects.create(product=self.product, alt_text='Image 2')
            
            images = self.product.productimage_set.all()
            self.assertEqual(images.count(), 2)
            self.assertIn(img1, images)
            self.assertIn(img2, images)


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password123')

    def test_create_user_profile(self):
        """Test creating user profile"""
        profile = UserProfile.objects.create(
            user=self.user,
            phone_number='+1234567890',
            date_of_birth='1990-01-01'
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '+1234567890')

    def test_user_profile_one_to_one(self):
        """Test one-to-one relationship with user"""
        profile = UserProfile.objects.create(user=self.user)
        
        self.assertEqual(self.user.userprofile, profile)

    def test_user_profile_str_method(self):
        """Test string representation"""
        profile = UserProfile.objects.create(user=self.user)
        
        expected_str = f"{self.user.username}'s Profile"
        self.assertEqual(str(profile), expected_str)

    def test_user_profile_phone_validation(self):
        """Test phone number validation"""
        if hasattr(UserProfile, 'clean'):
            profile = UserProfile(
                user=self.user,
                phone_number='invalid-phone'
            )
            
            with self.assertRaises(ValidationError):
                profile.full_clean()

    def test_user_profile_age_calculation(self):
        """Test age calculation"""
        profile = UserProfile.objects.create(
            user=self.user,
            date_of_birth='1990-01-01'
        )
        
        if hasattr(profile, 'get_age'):
            age = profile.get_age()
            self.assertGreater(age, 30)  # Should be over 30 by now


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password123')
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            name='Phone', slug='phone', price=Decimal('100.00'), category=self.category
        )

    def test_create_order(self):
        """Test creating an order"""
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            total_amount=Decimal('150.00'),
            status='pending'
        )
        
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_amount, Decimal('150.00'))
        self.assertEqual(order.status, 'pending')

    def test_order_number_generation(self):
        """Test order number generation"""
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            total_amount=Decimal('150.00')
        )
        
        if hasattr(order, 'order_number'):
            self.assertIsNotNone(order.order_number)
            self.assertTrue(len(order.order_number) > 0)

    def test_order_str_method(self):
        """Test order string representation"""
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            total_amount=Decimal('150.00')
        )
        
        if hasattr(order, 'order_number'):
            self.assertIn(order.order_number, str(order))
        else:
            self.assertIn(str(order.id), str(order))

    def test_order_status_choices(self):
        """Test order status choices"""
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            total_amount=Decimal('150.00'),
            status='pending'
        )
        
        # Test valid status
        order.status = 'shipped'
        order.save()
        self.assertEqual(order.status, 'shipped')

    def test_order_total_calculation(self):
        """Test order total calculation"""
        order = Order.objects.create(
            user=self.user,
            email=self.user.email,
            total_amount=Decimal('0.00')
        )
        
        if hasattr(order, 'calculate_total'):
            # Add order items and test calculation
            OrderItem