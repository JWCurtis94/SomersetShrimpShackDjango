import io
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from store.forms import (
    ProductForm, CategoryForm, CheckoutForm, ContactForm, CustomUserCreationForm
)
from store.models import Category, Product
from decimal import Decimal

class ProductFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Aquatic Plants", slug="aquatic-plants")
        self.img_data = b"\x47\x49\x46"  # GIF header
        self.good_img = SimpleUploadedFile("img.jpg", self.img_data, content_type="image/jpeg")
        self.bad_img = SimpleUploadedFile("img.txt", b"not an image", content_type="text/plain")

    def test_valid_product_form(self):
        form = ProductForm(data={
            "name": "Amazon Sword",
            "description": "Easy plant",
            "category": self.category.id,
            "price": Decimal("12.99"),
            "stock": 5,
            "available": True,
            "featured": False,
            "size": "medium",
        }, files={"image": self.good_img})
        self.assertTrue(form.is_valid())

    def test_duplicate_name_validation(self):
        Product.objects.create(
            name="Java Moss", slug="java-moss", price=3, category=self.category, stock=5
        )
        form = ProductForm(data={
            "name": "Java Moss",
            "description": "Nice moss",
            "category": self.category.id,
            "price": Decimal("3.99"),
            "stock": 5,
            "available": True,
            "featured": False,
            "size": "small",
        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_negative_price(self):
        form = ProductForm(data={
            "name": "Banana Plant",
            "description": "Aquatic",
            "category": self.category.id,
            "price": -5,
            "stock": 3,
            "available": True,
            "featured": False,
            "size": "medium",
        })
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)

    def test_negative_stock(self):
        form = ProductForm(data={
            "name": "Hornwort",
            "description": "Aquatic",
            "category": self.category.id,
            "price": 2.5,
            "stock": -4,
            "available": True,
            "featured": False,
            "size": "medium",
        })
        self.assertFalse(form.is_valid())
        self.assertIn('stock', form.errors)

    def test_image_too_large(self):
        bigfile = SimpleUploadedFile("big.jpg", b"x" * (2 * 1024 * 1024 + 1), content_type="image/jpeg")
        form = ProductForm(data={
            "name": "Vallisneria",
            "description": "Tall plant",
            "category": self.category.id,
            "price": 4,
            "stock": 1,
            "available": True,
            "featured": False,
        }, files={"image": bigfile})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_image_bad_type(self):
        form = ProductForm(data={
            "name": "Anacharis",
            "description": "Stem plant",
            "category": self.category.id,
            "price": 3,
            "stock": 2,
            "available": True,
            "featured": False,
        }, files={"image": self.bad_img})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

class CategoryFormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Fish", slug="fish")

    def test_valid_category_form(self):
        img = SimpleUploadedFile("cat.png", b"\x89PNG", content_type="image/png")
        form = CategoryForm(data={
            "name": "Crustaceans",
            "order": 1,
        }, files={"image": img})
        self.assertTrue(form.is_valid())

    def test_duplicate_name(self):
        Category.objects.create(name="Shrimp", slug="shrimp")
        form = CategoryForm(data={
            "name": "Shrimp",
            "order": 2,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_image_too_large(self):
        bigfile = SimpleUploadedFile("big.png", b"x" * (2 * 1024 * 1024 + 1), content_type="image/png")
        form = CategoryForm(data={"name": "Snails", "order": 3}, files={"image": bigfile})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_image_bad_type(self):
        form = CategoryForm(data={"name": "Crabs", "order": 4}, files={
            "image": SimpleUploadedFile("crab.txt", b"hi", content_type="text/plain")
        })
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

class CheckoutFormTests(TestCase):
    def test_valid_checkout(self):
        form = CheckoutForm(data={
            "email": "user@example.com",
            "phone": "+447123456789",
            "agree": True,
        })
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        form = CheckoutForm(data={
            "email": "bademail",
            "phone": "0777777777",
            "agree": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_agree_required(self):
        form = CheckoutForm(data={
            "email": "user@example.com",
            "phone": "0777777777",
            "agree": False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("agree", form.errors)

class ContactFormTests(TestCase):
    def test_valid_contact(self):
        form = ContactForm(data={
            "name": "Contact Name",
            "email": "mail@example.com",
            "subject": "Subject",
            "message": "A message"
        })
        self.assertTrue(form.is_valid())

    def test_missing_fields(self):
        form = ContactForm(data={"name": "", "email": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("subject", form.errors)
        self.assertIn("message", form.errors)

class CustomUserCreationFormTests(TestCase):
    def test_valid_user_creation(self):
        form = CustomUserCreationForm(data={
            "username": "user1",
            "email": "user1@example.com",
            "password1": "TestPassword123!",
            "password2": "TestPassword123!",
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, "user1@example.com")

    def test_duplicate_username(self):
        User.objects.create_user(username="user1", email="x@x.com", password="pass")
        form = CustomUserCreationForm(data={
            "username": "user1",
            "email": "user1@example.com",
            "password1": "TestPassword123!",
            "password2": "TestPassword123!",
        })
        self.assertFalse(form.is_valid())

    def test_password_mismatch(self):
        form = CustomUserCreationForm(data={
            "username": "user2",
            "email": "user2@example.com",
            "password1": "abc",
            "password2": "def",
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
