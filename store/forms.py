from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'stock', 'image', 'available', 'featured']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

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