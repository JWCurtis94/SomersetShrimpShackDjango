#!/usr/bin/env python
"""
Setup script to populate Somerset Shrimp Shack with products and categories
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Category, Product
from decimal import Decimal

def create_categories():
    """Create product categories for the shrimp shack"""
    categories_data = [
        {'name': 'Fresh Prawns & Shrimp', 'slug': 'fresh-prawns-shrimp', 'description': 'Fresh, locally sourced prawns and shrimp', 'order': 1},
        {'name': 'Frozen Seafood', 'slug': 'frozen-seafood', 'description': 'Premium frozen seafood selection', 'order': 2},
        {'name': 'Ready-to-Eat', 'slug': 'ready-to-eat', 'description': 'Pre-prepared seafood dishes', 'order': 3},
        {'name': 'Seafood Platters', 'slug': 'seafood-platters', 'description': 'Mixed seafood platters for sharing', 'order': 4},
        {'name': 'Seasonings & Sauces', 'slug': 'seasonings-sauces', 'description': 'Spices and sauces for seafood', 'order': 5}
    ]
    
    created_categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults={
                'name': cat_data['name'],
                'description': cat_data['description'],
                'order': cat_data['order']
            }
        )
        if created:
            print(f"✓ Created category: {category.name}")
        else:
            print(f"• Category already exists: {category.name}")
        created_categories.append(category)
    
    return created_categories

def create_products(categories):
    """Create products for each category"""
    cat_dict = {cat.slug: cat for cat in categories}
    
    products_data = [
        # Fresh Prawns & Shrimp
        {'name': 'King Prawns (Large)', 'slug': 'king-prawns-large', 'description': 'Fresh, locally caught king prawns. Perfect for grilling or stir-frying.', 'category': cat_dict['fresh-prawns-shrimp'], 'price': Decimal('18.99'), 'stock': 25},
        {'name': 'Tiger Prawns (Medium)', 'slug': 'tiger-prawns-medium', 'description': 'Sweet tiger prawns, ideal for curries and paellas.', 'category': cat_dict['fresh-prawns-shrimp'], 'price': Decimal('14.99'), 'stock': 30},
        {'name': 'Brown Shrimp', 'slug': 'brown-shrimp', 'description': 'Traditional Somerset brown shrimp, perfect for sandwiches.', 'category': cat_dict['fresh-prawns-shrimp'], 'price': Decimal('12.99'), 'stock': 20},
        {'name': 'Fresh Langoustines', 'slug': 'fresh-langoustines', 'description': 'Premium langoustines, sweet and delicate.', 'category': cat_dict['fresh-prawns-shrimp'], 'price': Decimal('24.99'), 'stock': 15},
        
        # Frozen Seafood
        {'name': 'Frozen Prawns (1kg)', 'slug': 'frozen-prawns-1kg', 'description': 'Convenient frozen prawns, ready to cook.', 'category': cat_dict['frozen-seafood'], 'price': Decimal('16.99'), 'stock': 40},
        {'name': 'Mixed Seafood Pack', 'slug': 'mixed-seafood-pack', 'description': 'A selection of frozen seafood including prawns, scallops, and squid.', 'category': cat_dict['frozen-seafood'], 'price': Decimal('22.99'), 'stock': 20},
        {'name': 'Frozen Scallops', 'slug': 'frozen-scallops', 'description': 'Premium frozen scallops, perfect for pan-frying.', 'category': cat_dict['frozen-seafood'], 'price': Decimal('19.99'), 'stock': 18},
        
        # Ready-to-Eat
        {'name': 'Prawn Cocktail (Serves 2)', 'slug': 'prawn-cocktail-serves-2', 'description': 'Classic prawn cocktail with Marie Rose sauce.', 'category': cat_dict['ready-to-eat'], 'price': Decimal('8.99'), 'stock': 12},
        {'name': 'Smoked Salmon & Prawn Terrine', 'slug': 'smoked-salmon-prawn-terrine', 'description': 'Luxury terrine perfect for special occasions.', 'category': cat_dict['ready-to-eat'], 'price': Decimal('15.99'), 'stock': 8},
        {'name': 'Seafood Salad', 'slug': 'seafood-salad', 'description': 'Fresh mixed seafood salad with herbs and lemon dressing.', 'category': cat_dict['ready-to-eat'], 'price': Decimal('11.99'), 'stock': 10},
        
        # Seafood Platters
        {'name': 'Family Seafood Platter', 'slug': 'family-seafood-platter', 'description': 'Large platter with prawns, crab, langoustines - serves 4-6.', 'category': cat_dict['seafood-platters'], 'price': Decimal('45.99'), 'stock': 5},
        {'name': 'Romantic Seafood Platter', 'slug': 'romantic-seafood-platter', 'description': 'Perfect for two, with champagne prawns and scallops.', 'category': cat_dict['seafood-platters'], 'price': Decimal('28.99'), 'stock': 8},
        
        # Seasonings & Sauces
        {'name': 'Garlic Butter Sauce', 'slug': 'garlic-butter-sauce', 'description': 'Rich garlic butter perfect for prawns and scallops.', 'category': cat_dict['seasonings-sauces'], 'price': Decimal('4.99'), 'stock': 50},
        {'name': 'Seafood Seasoning Mix', 'slug': 'seafood-seasoning-mix', 'description': 'Special blend of herbs and spices for seafood.', 'category': cat_dict['seasonings-sauces'], 'price': Decimal('6.99'), 'stock': 35},
        {'name': 'Marie Rose Sauce', 'slug': 'marie-rose-sauce', 'description': 'Classic prawn cocktail sauce.', 'category': cat_dict['seasonings-sauces'], 'price': Decimal('3.99'), 'stock': 40}
    ]
    
    created_products = []
    for prod_data in products_data:
        product, created = Product.objects.get_or_create(
            slug=prod_data['slug'],
            defaults={
                'name': prod_data['name'],
                'description': prod_data['description'],
                'category': prod_data['category'],
                'price': prod_data['price'],
                'stock': prod_data['stock'],
                'available': True
            }
        )
        if created:
            print(f"✓ Created product: {product.name} - £{product.price} (Stock: {product.stock})")
        else:
            print(f"• Product already exists: {product.name}")
        created_products.append(product)
    
    return created_products

def main():
    print("Somerset Shrimp Shack - Store Setup")
    print("=" * 40)
    
    print("\n📁 Creating Categories...")
    categories = create_categories()
    
    print(f"\n🛍️ Creating Products...")
    products = create_products(categories)
    
    print(f"\n✅ Setup Complete!")
    print(f"Created {len(categories)} categories and {len(products)} products")
    
    # Summary
    total_stock = sum(p.stock for p in products)
    print(f"\n📊 Summary:")
    print(f"• Categories: {Category.objects.count()}")
    print(f"• Products: {Product.objects.count()}")
    print(f"• Total Stock Items: {total_stock}")
    print(f"• Stock Value: £{sum(p.price * p.stock for p in products):.2f}")

if __name__ == '__main__':
    main()
