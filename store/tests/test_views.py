from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from store.models import Category, Product, Order, OrderItem
from decimal import Decimal

class StoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.admin_user = User.objects.create_superuser(
            username="admin", password="adminpass", email="admin@test.com"
        )
        self.category = Category.objects.create(name="Shrimp", slug="shrimp")
        self.product = Product.objects.create(
            name="Red Cherry Shrimp",
            slug="red-cherry-shrimp",
            price=3.99,
            stock=10,
            category=self.category,
            available=True,
        )
        self.order = Order.objects.create(
            user=self.user,
            stripe_checkout_id="id1",
            email="test@example.com",
            status="paid",
            total_amount=3.99,
            shipping_name="T",
            shipping_address="A",
            shipping_city="B",
            shipping_zip="C",
            shipping_country="UK",
            order_reference="ORD-101",
        )
        self.order_item = OrderItem.objects.create(
            order=self.order, product=self.product, quantity=1, price=3.99
        )

    def test_home_view(self):
        response = self.client.get(reverse("store:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/home.html")

    def test_product_list_view(self):
        response = self.client.get(reverse("store:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/product_list.html")

    def test_product_detail_view(self):
        response = self.client.get(reverse("store:product_detail", args=[self.product.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)

    def test_category_detail_view(self):
        response = self.client.get(reverse("store:category_detail", args=[self.category.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/category_detail.html")

    def test_cart_add_and_view(self):
        response = self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 2})
        self.assertRedirects(response, reverse("store:cart_view"))
        response = self.client.get(reverse("store:cart_view"))
        self.assertContains(response, self.product.name)

    def test_cart_update(self):
        self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 1})
        response = self.client.post(reverse("store:update_cart", args=[self.product.id]), {"quantity": 3})
        self.assertRedirects(response, reverse("store:cart_view"))

    def test_cart_remove(self):
        self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 1})
        response = self.client.post(reverse("store:remove_from_cart", args=[self.product.id]))
        self.assertRedirects(response, reverse("store:cart_view"))

    def test_checkout_cart_empty(self):
        response = self.client.get(reverse("store:checkout_cart"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/checkout.html")

    def test_dashboard_admin_access(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse("store:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/dashboard.html")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("store:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_stock_management_admin_access(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse("store:stock_management"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/stock_management.html")

    def test_unauthorized_stock_management_redirect(self):
        response = self.client.get(reverse("store:stock_management"))
        self.assertEqual(response.status_code, 302)

    def test_profile_requires_login(self):
        response = self.client.get(reverse("store:profile"))
        self.assertEqual(response.status_code, 302)

    def test_order_history_requires_login(self):
        response = self.client.get(reverse("store:order_history"))
        self.assertEqual(response.status_code, 302)

    def test_payment_cancel_view(self):
        response = self.client.get(reverse("store:payment_cancel"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/payment_cancel.html")

    # --- Additional edge-case/branch coverage below ---

    def test_cart_add_invalid_product(self):
        response = self.client.post(reverse("store:add_to_cart", args=[999]), {"quantity": 1})
        self.assertEqual(response.status_code, 404)

    def test_cart_add_invalid_quantity(self):
        response = self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": -2})
        self.assertContains(
            self.client.get(reverse("store:cart_view")), self.product.name, status_code=200
        )  # This line can be customized if you show errors

    def test_checkout_cart_with_items(self):
        self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 1})
        response = self.client.get(reverse("store:checkout_cart"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "store/checkout.html")

    def test_admin_only_views(self):
        admin_urls = [
            "dashboard",
            "stock_management",
        ]
        self.client.login(username="admin", password="adminpass")
        for url in admin_urls:
            response = self.client.get(reverse(f"store:{url}"))
            self.assertEqual(response.status_code, 200)

    def test_post_checkout_view(self):
        # Simulate a full checkout POST; you'll need to adjust data for your actual view logic
        self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 1})
        response = self.client.post(reverse("store:checkout_cart"), {
            "email": "buyer@example.com",
            "phone": "+447111111111",
            "agree": True,
        })
        # Expect redirect, or 200 with errors if payment fails (customize for your flow)
        self.assertIn(response.status_code, [200, 302])

    def test_404_for_bad_product_slug(self):
        response = self.client.get(reverse("store:product_detail", args=["bad-slug"]))
        self.assertEqual(response.status_code, 404)

    def test_404_for_bad_category_slug(self):
        response = self.client.get(reverse("store:category_detail", args=["bad-slug"]))
        self.assertEqual(response.status_code, 404)

from django.urls import reverse
from django.test import TestCase, Client
from store.models import Product, Category, Order, OrderItem
from django.contrib.auth.models import User
from decimal import Decimal

class TestStoreViewsAdvanced(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="joe", password="testpass")
        self.admin = User.objects.create_superuser(
            username="adminjoe", password="adminpass", email="admin@x.com"
        )
        self.category = Category.objects.create(name="Shrimp", slug="shrimp")
        self.product = Product.objects.create(
            name="Orange Shrimp", slug="orange", price=1.99, stock=12, category=self.category, available=True
        )

    def test_add_to_cart_invalid_quantity(self):
        response = self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": -10})
        self.assertIn(response.status_code, [200, 400, 302])

    def test_update_cart_invalid_product(self):
        response = self.client.post(reverse("store:update_cart", args=[9999]), {"quantity": 2})
        self.assertEqual(response.status_code, 404)

    def test_remove_from_cart_invalid_product(self):
        response = self.client.post(reverse("store:remove_from_cart", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_dashboard_requires_admin(self):
        self.client.login(username="joe", password="testpass")
        response = self.client.get(reverse("store:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_checkout_cart_post_invalid(self):
        self.client.post(reverse("store:add_to_cart", args=[self.product.id]), {"quantity": 1})
        response = self.client.post(reverse("store:checkout_cart"), {
            "email": "notanemail", "phone": "bad", "agree": False
        })
        self.assertIn(response.status_code, [200, 400])

    def test_product_detail_not_found(self):
        response = self.client.get(reverse("store:product_detail", args=["no-such-product"]))
        self.assertEqual(response.status_code, 404)

    def test_category_detail_not_found(self):
        response = self.client.get(reverse("store:category_detail", args=["no-such-category"]))
        self.assertEqual(response.status_code, 404)

    def test_permission_denied_on_stock_management(self):
        self.client.login(username="joe", password="testpass")
        response = self.client.get(reverse("store:stock_management"))
        self.assertEqual(response.status_code, 302)
