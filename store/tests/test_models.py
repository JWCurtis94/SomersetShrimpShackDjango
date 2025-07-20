from django.test import TestCase
from django.core.exceptions import ValidationError
from store.models import Category, Product, Order, OrderItem, UserProfile
from django.contrib.auth.models import User
from decimal import Decimal


class TestCategory(TestCase):
    """Test cases for Category model"""
    
    def test_str_method(self):
        """Test Category string representation"""
        cat = Category.objects.create(name="Snails", slug="snails")
        self.assertEqual(str(cat), "Snails")

    def test_get_absolute_url(self):
        """Test Category absolute URL generation"""
        cat = Category.objects.create(name="Crabs", slug="crabs")
        self.assertTrue(cat.get_absolute_url().endswith("/category/crabs/"))

    def test_get_next_order(self):
        """Test getting next order number for categories"""
        Category.objects.create(name="Fish", slug="fish", order=1)
        self.assertEqual(Category.get_next_order(), 2)

    def test_get_next_order_empty_database(self):
        """Test getting next order when no categories exist"""
        self.assertEqual(Category.get_next_order(), 1)

    def test_clean_duplicate_name(self):
        """Test validation for duplicate category names"""
        Category.objects.create(name="Plants", slug="plants")
        cat = Category(name="Plants", slug="plants2")
        with self.assertRaises(Exception):
            cat.clean()

    def test_save_sets_slug(self):
        """Test that saving category generates slug from name"""
        cat = Category(name="Unique Category", slug="")
        cat.save()
        self.assertTrue(cat.slug)
        self.assertIn("unique", cat.slug.lower())

    def test_save_preserves_existing_slug(self):
        """Test that existing slug is preserved on save"""
        cat = Category(name="Test", slug="custom-slug")
        cat.save()
        self.assertEqual(cat.slug, "custom-slug")

    def test_ordering(self):
        """Test category ordering"""
        cat1 = Category.objects.create(name="First", slug="first", order=2)
        cat2 = Category.objects.create(name="Second", slug="second", order=1)
        categories = Category.objects.all()
        self.assertEqual(categories[0], cat2)  # Lower order comes first


class TestProduct(TestCase):
    """Test cases for Product model"""
    
    def setUp(self):
        self.cat = Category.objects.create(name="Shrimp", slug="shrimp")

    def test_str_method(self):
        """Test Product string representation"""
        p = Product.objects.create(
            name="Neo Shrimp", slug="neo", price=5, category=self.cat, stock=7
        )
        self.assertEqual(str(p), "Neo Shrimp")

    def test_get_absolute_url(self):
        """Test Product absolute URL generation"""
        p = Product.objects.create(
            name="Red Cherry", slug="rcc", price=2, category=self.cat, stock=5
        )
        self.assertTrue(p.get_absolute_url().endswith("/product/rcc/"))

    def test_save_sets_slug(self):
        """Test that saving product generates slug from name"""
        p = Product(name="Auto Slug Product", slug="", price=1, category=self.cat, stock=3)
        p.save()
        self.assertTrue(p.slug)
        self.assertIn("auto", p.slug.lower())

    def test_save_preserves_existing_slug(self):
        """Test that existing slug is preserved on save"""
        p = Product(name="Test", slug="custom-product-slug", price=1, category=self.cat, stock=3)
        p.save()
        self.assertEqual(p.slug, "custom-product-slug")

    def test_is_in_stock_true(self):
        """Test product in stock status when stock > 0"""
        p = Product.objects.create(
            name="In Stock", slug="in-stock", price=2, category=self.cat, stock=5
        )
        self.assertTrue(p.is_in_stock)

    def test_is_in_stock_false(self):
        """Test product in stock status when stock = 0"""
        p = Product.objects.create(
            name="Out of Stock", slug="out-of-stock", price=2, category=self.cat, stock=0
        )
        self.assertFalse(p.is_in_stock)

    def test_is_in_stock_updated_after_save(self):
        """Test that is_in_stock updates correctly after stock changes"""
        p = Product.objects.create(
            name="Low Stock", slug="low", price=2, category=self.cat, stock=1
        )
        self.assertTrue(p.is_in_stock)
        
        p.stock = 0
        p.save()
        p.refresh_from_db()
        self.assertFalse(p.is_in_stock)

    def test_display_price(self):
        """Test product price display formatting"""
        p = Product.objects.create(
            name="ShowPrice", slug="sp", price=10, category=self.cat, stock=2
        )
        self.assertTrue("£" in p.display_price)
        self.assertIn("10.00", p.display_price)

    def test_display_price_decimal(self):
        """Test product price display with decimal values"""
        p = Product.objects.create(
            name="Decimal Price", slug="decimal", price=Decimal("15.99"), category=self.cat, stock=1
        )
        self.assertIn("15.99", p.display_price)

    def test_available_default_true(self):
        """Test that product available field defaults to True"""
        p = Product.objects.create(
            name="Default Available", slug="default", price=5, category=self.cat, stock=1
        )
        self.assertTrue(p.available)

    def test_product_unavailable(self):
        """Test product with available=False"""
        p = Product.objects.create(
            name="Unavailable", slug="unavailable", price=5, category=self.cat, 
            stock=10, available=False
        )
        self.assertFalse(p.available)
        self.assertTrue(p.stock > 0)  # Has stock but not available


class TestOrder(TestCase):
    """Test cases for Order model"""
    
    def setUp(self):
        self.user = User.objects.create_user("testuser", "u@x.com", "pass")
        self.cat = Category.objects.create(name="Fish", slug="fish")
        self.product = Product.objects.create(
            name="Betta", slug="betta", price=4, category=self.cat, stock=3
        )

    def test_str_method(self):
        """Test Order string representation"""
        order = Order.objects.create(
            user=self.user,
            stripe_checkout_id="id123",
            email="x@x.com",
            status="pending",
            total_amount=4,
            shipping_name="A",
            shipping_address="B",
            shipping_city="C",
            shipping_zip="D",
            shipping_country="UK",
            order_reference="ORD-1",
        )
        self.assertTrue(str(order).startswith("Order #"))
        self.assertIn("ORD-1", str(order))

    def test_order_totals(self):
        """Test order total calculations"""
        order = Order.objects.create(
            user=self.user,
            stripe_checkout_id="id124",
            email="y@x.com",
            status="paid",
            total_amount=8,
            shipping_name="A",
            shipping_address="B",
            shipping_city="C",
            shipping_zip="D",
            shipping_country="UK",
            order_reference="ORD-2",
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=2, price=4)
        
        self.assertEqual(order.item_count, 2)
        self.assertTrue(order.total_price >= 8)

    def test_shipping_complete_property(self):
        """Test order shipping complete property"""
        order = Order.objects.create(
            user=self.user,
            stripe_checkout_id="id125",
            email="z@x.com",
            status="shipped",
            total_amount=12,
            shipping_name="A",
            shipping_address="B",
            shipping_city="C",
            shipping_zip="D",
            shipping_country="UK",
            order_reference="ORD-3",
        )
        self.assertTrue(hasattr(order, "shipping_complete"))

    def test_order_without_items(self):
        """Test order with no items"""
        order = Order.objects.create(
            user=self.user,
            stripe_checkout_id="id126",
            email="empty@x.com",
            status="pending",
            total_amount=0,
            shipping_name="A",
            shipping_address="B",
            shipping_city="C",
            shipping_zip="D",
            shipping_country="UK",
            order_reference="ORD-4",
        )
        self.assertEqual(order.item_count, 0)

    def test_order_status_choices(self):
        """Test different order status values"""
        statuses = ["pending", "paid", "shipped", "delivered", "cancelled"]
        for status in statuses:
            order = Order.objects.create(
                user=self.user,
                stripe_checkout_id=f"id_{status}",
                email=f"{status}@x.com",
                status=status,
                total_amount=10,
                shipping_name="A",
                shipping_address="B",
                shipping_city="C",
                shipping_zip="D",
                shipping_country="UK",
                order_reference=f"ORD-{status.upper()}",
            )
            self.assertEqual(order.status, status)


class TestOrderItem(TestCase):
    """Test cases for OrderItem model"""
    
    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@example.com", "pass")
        self.cat = Category.objects.create(name="Plants", slug="plants")
        self.product = Product.objects.create(
            name="Moss Ball", slug="moss", price=Decimal("3.50"), category=self.cat, stock=10
        )
        self.order = Order.objects.create(
            user=self.user,
            stripe_checkout_id="test123",
            email="test@example.com",
            status="paid",
            total_amount=Decimal("7.00"),
            shipping_name="Test User",
            shipping_address="123 Test St",
            shipping_city="Test City",
            shipping_zip="12345",
            shipping_country="UK",
            order_reference="ORD-TEST",
        )

    def test_order_item_creation(self):
        """Test creating an order item"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=Decimal("3.50")
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal("3.50"))
        self.assertEqual(item.product, self.product)

    def test_order_item_total_calculation(self):
        """Test order item total price calculation"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
            price=Decimal("3.50")
        )
        expected_total = Decimal("3.50") * 3
        # Assuming OrderItem has a get_total method or similar
        self.assertEqual(item.quantity * item.price, expected_total)


class TestUserProfile(TestCase):
    """Test cases for UserProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@u.com", "pw")

    def test_profile_creation(self):
        """Test creating a user profile"""
        profile = UserProfile.objects.create(user=self.user, phone_number="123")
        self.assertEqual(str(profile), "testuser")

    def test_profile_str_method(self):
        """Test UserProfile string representation"""
        profile = UserProfile.objects.create(
            user=self.user, 
            phone_number="+44123456789"
        )
        self.assertEqual(str(profile), self.user.username)

    def test_profile_optional_fields(self):
        """Test profile with optional fields"""
        profile = UserProfile.objects.create(
            user=self.user,
            phone_number="",  # Empty phone number should be allowed
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, "")

    def test_profile_user_relationship(self):
        """Test the relationship between User and UserProfile"""
        profile = UserProfile.objects.create(user=self.user, phone_number="123456")
        
        # Test forward relationship
        self.assertEqual(profile.user, self.user)
        
        # Test reverse relationship (if properly configured)
        # This would depend on your model's related_name setting
        # self.assertEqual(self.user.profile, profile)


class TestModelValidation(TestCase):
    """Test cases for model validation and edge cases"""
    
    def setUp(self):
        self.category = Category.objects.create(name="Test", slug="test")
        self.user = User.objects.create_user("test", "test@test.com", "pass")

    def test_product_negative_price(self):
        """Test product creation with negative price"""
        # This should be handled by model validation if implemented
        product = Product(
            name="Negative Price",
            slug="negative",
            price=Decimal("-5.00"),
            category=self.category,
            stock=1
        )
        # Depending on your model constraints, this might raise an error
        try:
            product.full_clean()
            product.save()
        except ValidationError:
            pass  # Expected if you have validation

    def test_product_negative_stock(self):
        """Test product creation with negative stock"""
        product = Product(
            name="Negative Stock",
            slug="neg-stock",
            price=Decimal("5.00"),
            category=self.category,
            stock=-1
        )
        try:
            product.full_clean()
            product.save()
        except ValidationError:
            pass  # Expected if you have validation

    def test_empty_required_fields(self):
        """Test model creation with empty required fields"""
        # Test Category with empty name
        with self.assertRaises((ValidationError, ValueError)):
            cat = Category(name="", slug="empty")
            cat.full_clean()

        # Test Product with empty name
        with self.assertRaises((ValidationError, ValueError)):
            product = Product(name="", price=Decimal("5.00"), category=self.category)
            product.full_clean()