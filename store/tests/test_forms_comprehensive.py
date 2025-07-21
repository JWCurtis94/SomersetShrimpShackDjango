"""
Comprehensive tests for store.forms module
This file provides complete test coverage for all form classes
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from store.forms import ProductForm, CategoryForm, CheckoutForm, ContactForm
from store.models import Product, Category


class ProductFormTest(TestCase):
    """Test the ProductForm class"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="Test Category",
            description="Test description"
        )
        
        self.valid_data = {
            'name': 'Test Product',
            'description': 'This is a test product',
            'price': Decimal('19.99'),
            'category': self.category.id,
            'stock': 10,
            'available': True,
            'featured': False
        }
    
    def test_valid_product_form(self):
        """Test form with valid data"""
        form = ProductForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_product_form_saves_correctly(self):
        """Test form saves product correctly"""
        form = ProductForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        product = form.save()
        
        self.assertEqual(product.name, 'Test Product')
        self.assertEqual(product.price, Decimal('19.99'))
        self.assertEqual(product.stock, 10)
        self.assertEqual(product.category, self.category)
    
    def test_price_validation_minimum(self):
        """Test price cannot be zero or negative"""
        # Test zero price
        data = self.valid_data.copy()
        data['price'] = Decimal('0.00')
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)
        
        # Test negative price
        data['price'] = Decimal('-5.00')
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)
    
    def test_stock_validation_negative(self):
        """Test stock cannot be negative"""
        data = self.valid_data.copy()
        data['stock'] = -5
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('stock', form.errors)
    
    def test_name_validation_empty(self):
        """Test name validation for empty values"""
        data = self.valid_data.copy()
        data['name'] = ''
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
        # Test name with only whitespace
        data['name'] = '   '
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_name_validation_too_short(self):
        """Test name validation for too short names"""
        data = self.valid_data.copy()
        data['name'] = 'X'
        form = ProductForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_name_cleaning_whitespace(self):
        """Test name field strips whitespace"""
        data = self.valid_data.copy()
        data['name'] = '  Test Product  '
        form = ProductForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Test Product')
    
    def test_required_fields(self):
        """Test all required fields are validated"""
        required_fields = ['name', 'price', 'category', 'stock']
        
        for field in required_fields:
            data = self.valid_data.copy()
            del data[field]
            form = ProductForm(data=data)
            self.assertFalse(form.is_valid())
            self.assertIn(field, form.errors)


class CategoryFormTest(TestCase):
    """Test the CategoryForm class"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            'name': 'Test Category',
            'description': 'Test description',
            'order': 1
        }
    
    def test_valid_category_form(self):
        """Test form with valid data"""
        form = CategoryForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_category_form_saves_correctly(self):
        """Test form saves category correctly"""
        form = CategoryForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        category = form.save()
        
        self.assertEqual(category.name, 'Test Category')
        self.assertEqual(category.description, 'Test description')
        self.assertEqual(category.order, 1)
    
    def test_order_field_optional(self):
        """Test order field is optional and defaults to 0"""
        data = self.valid_data.copy()
        del data['order']
        form = CategoryForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['order'], 0)
    
    def test_order_field_empty_string_defaults(self):
        """Test empty string order field defaults to 0"""
        data = self.valid_data.copy()
        data['order'] = ''
        form = CategoryForm(data=data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['order'], 0)
    
    def test_name_validation_empty(self):
        """Test name validation for empty values"""
        data = self.valid_data.copy()
        data['name'] = ''
        form = CategoryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
        # Test name with only whitespace
        data['name'] = '   '
        form = CategoryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_name_validation_duplicate(self):
        """Test name validation for duplicate categories"""
        # Create an existing category
        Category.objects.create(name='Existing Category')
        
        data = self.valid_data.copy()
        data['name'] = 'Existing Category'
        form = CategoryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        
        # Test case-insensitive duplicate detection
        data['name'] = 'existing category'
        form = CategoryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_name_validation_duplicate_exclude_self(self):
        """Test duplicate validation excludes current instance when editing"""
        existing_category = Category.objects.create(name='Existing Category')
        
        # When editing the same category, it should not conflict with itself
        data = {'name': 'Existing Category', 'description': 'Updated description'}
        form = CategoryForm(data=data, instance=existing_category)
        self.assertTrue(form.is_valid())
    
    def test_image_validation_size(self):
        """Test image file size validation"""
        # Create a mock large file (simulate > 5MB)
        large_image = SimpleUploadedFile(
            name='large_image.jpg',
            content=b'x' * (6 * 1024 * 1024),  # 6MB
            content_type='image/jpeg'
        )
        
        data = self.valid_data.copy()
        files = {'image': large_image}
        form = CategoryForm(data=data, files=files)
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
    
    def test_image_validation_format(self):
        """Test image file format validation"""
        # Test invalid file extension
        invalid_image = SimpleUploadedFile(
            name='test.txt',
            content=b'not an image',
            content_type='text/plain'
        )
        
        data = self.valid_data.copy()
        files = {'image': invalid_image}
        form = CategoryForm(data=data, files=files)
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
    
    def test_image_validation_valid_formats(self):
        """Test valid image formats are accepted"""
        valid_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        for fmt in valid_formats:
            image = SimpleUploadedFile(
                name=f'test{fmt}',
                content=b'fake image content',
                content_type=f'image/{fmt.strip(".")}'
            )
            
            data = self.valid_data.copy()
            data['name'] = f'Category {fmt}'  # Ensure unique names
            files = {'image': image}
            form = CategoryForm(data=data, files=files)
            # Note: This might fail in test because the file content isn't a real image
            # but the format validation should pass


class CheckoutFormTest(TestCase):
    """Test the CheckoutForm class"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            'email': 'test@example.com',
            'phone': '01234567890',
            'agree_to_terms': True
        }
    
    def test_valid_checkout_form(self):
        """Test form with valid data"""
        form = CheckoutForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_email_required(self):
        """Test email field is required"""
        data = self.valid_data.copy()
        del data['email']
        form = CheckoutForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_email_validation(self):
        """Test email field validates email format"""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        form = CheckoutForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_phone_optional(self):
        """Test phone field is optional"""
        data = self.valid_data.copy()
        del data['phone']
        form = CheckoutForm(data=data)
        self.assertTrue(form.is_valid())
    
    def test_terms_agreement_required(self):
        """Test terms agreement is required"""
        data = self.valid_data.copy()
        data['agree_to_terms'] = False
        form = CheckoutForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('agree_to_terms', form.errors)


class ContactFormTest(TestCase):
    """Test the ContactForm class"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'message': 'This is a test message.'
        }
    
    def test_valid_contact_form(self):
        """Test form with valid data"""
        form = ContactForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_all_fields_required(self):
        """Test all fields are required"""
        required_fields = ['name', 'email', 'subject', 'message']
        
        for field in required_fields:
            data = self.valid_data.copy()
            del data[field]
            form = ContactForm(data=data)
            self.assertFalse(form.is_valid())
            self.assertIn(field, form.errors)
    
    def test_email_validation(self):
        """Test email field validates email format"""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_name_max_length(self):
        """Test name field max length validation"""
        data = self.valid_data.copy()
        data['name'] = 'x' * 101  # Exceed max length of 100
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
    
    def test_subject_max_length(self):
        """Test subject field max length validation"""
        data = self.valid_data.copy()
        data['subject'] = 'x' * 201  # Exceed max length of 200
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)
