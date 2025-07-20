from django.test import TestCase
from django.contrib.admin.sites import site
from store.models import Product

class AdminTestCase(TestCase):
    def test_product_admin_registered(self):
        self.assertIn(Product, site._registry)
