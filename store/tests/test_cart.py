from django.test import TestCase, RequestFactory
from decimal import Decimal
from store.models import Product, Category
from store.cart import Cart, CartItem
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils import timezone
import datetime

print("CART MODULE:", Cart.__module__)


class TestCart(TestCase):
    """Test cases for the Cart functionality"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        # Apply session middleware to fake request
        middleware = SessionMiddleware()
        middleware.process_request(self.request)
        self.request.session.save()

        self.category = Category.objects.create(name="Plants", slug="plants")
        self.product = Product.objects.create(
            name="Anubias",
            price=Decimal("5.00"),
            stock=20,
            slug="anubias",
            category=self.category,
            available=True,
        )
        self.other_product = Product.objects.create(
            name="Java Fern",
            price=Decimal("3.00"),
            stock=30,
            slug="java-fern",
            category=self.category,
            available=True,
        )
        self.cart = Cart(self.request)

    def test_add_and_len(self):
        """Test adding items to cart and checking length"""
        self.cart.add(self.product, quantity=2)
        self.assertEqual(len(self.cart), 2)
        
        self.cart.add(self.product, quantity=1)
        self.assertEqual(len(self.cart), 3)
        
        self.cart.add(self.other_product, quantity=1)
        self.assertEqual(len(self.cart), 4)

    def test_add_override_quantity_true(self):
        """Test adding items with quantity override enabled"""
        self.cart.add(self.product, quantity=2)
        self.cart.add(self.product, quantity=5, override_quantity=True)
        items = self.cart.get_cart_items()
        self.assertEqual(items[0].quantity, 5)

    def test_add_override_quantity_false(self):
        """Test adding items with quantity override disabled"""
        self.cart.add(self.product, quantity=1)
        self.cart.add(self.product, quantity=2, override_quantity=False)
        items = self.cart.get_cart_items()
        self.assertEqual(items[0].quantity, 3)

    def test_add_with_size(self):
        """Test adding items with size specification"""
        self.cart.add(self.product, quantity=1, size="large")
        items = self.cart.get_cart_items()
        self.assertEqual(items[0].size, "large")

    def test_remove(self):
        """Test removing items from cart"""
        self.cart.add(self.product, quantity=2)
        self.cart.remove(self.product)
        self.assertEqual(len(self.cart), 0)

    def test_update_quantity(self):
        """Test updating item quantity in cart"""
        self.cart.add(self.product, quantity=1)
        self.cart.update(self.product, quantity=7)
        items = self.cart.get_cart_items()
        self.assertEqual(items[0].quantity, 7)

    def test_update_to_zero_removes_item(self):
        """Test that updating quantity to zero removes the item"""
        self.cart.add(self.product, quantity=2)
        self.cart.update(self.product, quantity=0)
        self.assertEqual(len(self.cart), 0)

    def test_update_negative_quantity_removes_item(self):
        """Test that negative quantity removes the item"""
        self.cart.add(self.product, quantity=2)
        self.cart.update(self.product, quantity=-5)
        self.assertEqual(len(self.cart), 0)

    def test_contains(self):
        """Test cart contains functionality"""
        self.cart.add(self.product, quantity=1)
        self.assertIn(self.product, self.cart)
        self.assertNotIn(self.other_product, self.cart)

    def test_iter(self):
        """Test cart iteration functionality"""
        self.cart.add(self.product, quantity=2)
        self.cart.add(self.other_product, quantity=1)
        items = list(iter(self.cart))
        self.assertEqual(len(items), 2)
        self.assertIsInstance(items[0], CartItem)
        
        # Test iteration with contains
        for item in self.cart:
            self.assertIn(item.product, [self.product, self.other_product])

    def test_subtotal_property(self):
        """Test cart subtotal calculation"""
        self.cart.add(self.product, quantity=2)
        self.cart.add(self.other_product, quantity=1)
        expected = Decimal("5.00") * 2 + Decimal("3.00")
        self.assertEqual(self.cart.subtotal, expected)

    def test_discount_property(self):
        """Test cart discount property"""
        self.assertEqual(self.cart.discount, Decimal("0.00"))

    def test_get_shipping_cost(self):
        """Test shipping cost calculation for aquarium store"""
        # Empty cart should have no shipping
        self.assertEqual(self.cart.get_shipping_cost(), Decimal("0.00"))
        
        # Add a live animal (should be £12)
        self.cart.add(self.product, quantity=1)
        self.assertEqual(self.cart.get_shipping_cost(), Decimal("12.00"))

    def test_final_total(self):
        """Test final total calculation including shipping"""
        self.cart.add(self.product, quantity=1)
        expected = Decimal("5.00") + Decimal("12.00")  # Product + live animal shipping
        self.assertEqual(self.cart.final_total, expected)

    def test_clear(self):
        """Test clearing all items from cart"""
        self.cart.add(self.product, quantity=2)
        self.cart.clear()
        self.assertEqual(len(self.cart), 0)

    def test_cleanup_expired(self):
        """Test cleanup of expired cart items"""
        # Simulate an old cart timestamp
        past = (timezone.now() - datetime.timedelta(days=8)).isoformat()
        self.request.session['cart_timestamp'] = past
        self.cart.add(self.product)
        
        # Create new cart to trigger cleanup
        new_cart = Cart(self.request)
        new_cart._cleanup_expired()
        self.assertTrue('cart' in new_cart.session)
        self.assertTrue('cart_timestamp' in new_cart.session)

    def test_missing_product(self):
        """Test handling of missing products in cart"""
        self.cart.add(self.product, quantity=1)
        # Delete the product from DB to simulate missing product
        self.product.delete()
        items = self.cart.get_cart_items()
        self.assertEqual(items, [])  # Missing product should be removed

    def test_get_cart_items_empty(self):
        """Test getting items from empty cart"""
        items = self.cart.get_cart_items()
        self.assertEqual(items, [])

    def test_build_key_default_and_size(self):
        """Test cart key building with different sizes"""
        key1 = self.cart._build_key(self.product.id, None)
        key2 = self.cart._build_key(self.product.id, "large")
        self.assertTrue(key1.endswith("default"))
        self.assertTrue(key2.endswith("large"))
        self.assertIsInstance(key1, str)
        self.assertIsInstance(key2, str)

    def test_handles_invalid_timestamp(self):
        """Test handling of invalid cart timestamp"""
        self.request.session['cart_timestamp'] = "notadatetime"
        Cart(self.request)  # Should not crash

    def test_save_sets_modified(self):
        """Test that saving cart sets session as modified"""
        self.cart.add(self.product, quantity=1)
        self.assertTrue(self.request.session.modified)

    def test_save_method(self):
        """Test explicit cart save method"""
        self.cart.add(self.product, quantity=2)
        self.cart.save()
        # Session should be saved


class TestCartItem(TestCase):
    """Test cases for CartItem functionality"""
    
    def setUp(self):
        self.category = Category.objects.create(name="Shrimp", slug="shrimp")
        self.product = Product.objects.create(
            name="Crystal Red Shrimp",
            price=Decimal("2.00"),
            stock=5,
            slug="crs",
            category=self.category,
            available=True,
        )

    def test_str_and_price(self):
        """Test CartItem string representation and price methods"""
        item = CartItem(
            product=self.product, 
            quantity=3, 
            size="medium", 
            stored_price=Decimal("7.00")
        )
        self.assertEqual(str(item), "3 x Crystal Red Shrimp (medium)")
        self.assertEqual(item.price, Decimal("7.00"))
        self.assertEqual(item.total_price, Decimal("21.00"))

    def test_methods_and_properties_no_stored_price(self):
        """Test CartItem when no stored price is provided"""
        item = CartItem(product=self.product, quantity=3, size=None, stored_price=None)
        self.assertIsInstance(str(item), str)
        self.assertEqual(item.price, self.product.price)
        self.assertEqual(item.total_price, self.product.price * 3)

    def test_str_without_size(self):
        """Test CartItem string representation without size"""
        item = CartItem(product=self.product, quantity=2, size=None, stored_price=None)
        self.assertIn(self.product.name, str(item))
        self.assertNotIn("(", str(item))  # No size specification in parentheses


class TestCartIntegration(TestCase):
    """Integration tests for Cart with Django test client"""
    
    def setUp(self):
        self.category = Category.objects.create(name="Test", slug="test")
        self.product = Product.objects.create(
            name="Test Product",
            price=Decimal("10.00"),
            stock=5,
            slug="test-product",
            category=self.category,
            available=True,
        )

    def test_cart_with_client_session(self):
        """Test cart functionality with Django test client session"""
        factory = RequestFactory()
        request = factory.get("/")
        request.session = self.client.session
        
        cart = Cart(request)
        cart.add(self.product, quantity=1)
        
        self.assertEqual(len(cart), 1)
        items = cart.get_cart_items()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].product, self.product)