from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Product, Category

class ProductForm(forms.ModelForm):
    # Add proper validators to price field
    price = forms.DecimalField(
        validators=[MinValueValidator(0.01)], 
        decimal_places=2, 
        max_digits=10,
        help_text="Price must be greater than £0.01"
    )
    
    # Add validators to stock field  
    stock = forms.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Stock cannot be negative"
    )
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'stock', 'image', 'available', 'featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'maxlength': 1000}),
            'name': forms.TextInput(attrs={'maxlength': 255}),
        }
    
    def clean_name(self):
        """Validate product name"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if not name:
                raise forms.ValidationError('Product name cannot be empty.')
            if len(name) < 2:
                raise forms.ValidationError('Product name must be at least 2 characters long.')
        return name

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make order field optional with default value
        self.fields['order'].required = False
        self.fields['order'].initial = 0
    
    def clean_order(self):
        """Ensure order field has a default value"""
        order = self.cleaned_data.get('order')
        if order is None or order == '':
            return 0
        return order
    
    def clean_name(self):
        """Validate category name"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if not name:
                raise forms.ValidationError('Category name cannot be empty.')
            
            # Check for duplicate names (case-insensitive)
            existing_query = Category.objects.filter(name__iexact=name)
            if self.instance and self.instance.pk:
                existing_query = existing_query.exclude(pk=self.instance.pk)
            
            if existing_query.exists():
                raise forms.ValidationError('A category with this name already exists.')
        
        return name
    
    def clean_image(self):
        """Validate the image field"""
        image = self.cleaned_data.get('image')
        if image:
            # Check file size (max 5MB)
            if hasattr(image, 'size') and image.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image file too large. Maximum size is 5MB.')
            
            # Check file extension
            if hasattr(image, 'name'):
                valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                file_name = image.name.lower()
                if not any(file_name.endswith(ext) for ext in valid_extensions):
                    raise forms.ValidationError(f'Invalid image format. Allowed formats: {", ".join(valid_extensions)}')
        
        return image

class CheckoutForm(forms.Form):
    email = forms.EmailField(label='Email Address', required=True)
    phone = forms.CharField(label='Phone Number', required=False)
    agree_to_terms = forms.BooleanField(
        label='I agree to the terms and conditions',
        required=True
    )

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    subject = forms.CharField(max_length=200, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)