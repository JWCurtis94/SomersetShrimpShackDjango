#!/usr/bin/env python
"""
Script to create the missing categories for Somerset Shrimp Shack
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Category

# Categories to create based on the navigation menu
categories = [
    {
        'name': 'Neocaridina Shrimp',
        'description': 'Hardy and colorful freshwater shrimp perfect for beginners. Includes Cherry Shrimp, Blue Dream, Yellow Fire, and more.',
        'slug': 'neocaridina-shrimp'
    },
    {
        'name': 'Caridina Shrimp',
        'description': 'Specialized freshwater shrimp requiring precise water parameters. Includes Crystal Red/Black, Taiwan Bee, Tiger Shrimp.',
        'slug': 'caridina-shrimp'
    },
    {
        'name': 'Floating Plants',
        'description': 'Easy-care aquatic plants that float on the water surface, providing shade and natural filtration.',
        'slug': 'floating-plants'
    },
    {
        'name': 'Stem Plants',
        'description': 'Versatile aquatic plants that can be planted in substrate or allowed to float.',
        'slug': 'stem-plants'
    },
    {
        'name': 'Rosette Plants',
        'description': 'Beautiful aquatic plants that grow in a rosette pattern from a central crown.',
        'slug': 'rosette-plants'
    },
    {
        'name': 'Botanicals',
        'description': 'Natural materials like leaves, pods, and bark to create a natural aquarium environment.',
        'slug': 'botanicals'
    },
    {
        'name': 'Food',
        'description': 'Specialized foods and supplements for freshwater shrimp and aquatic animals.',
        'slug': 'food'
    },
    {
        'name': 'Merchandise',
        'description': 'Somerset Shrimp Shack branded merchandise and aquarium accessories.',
        'slug': 'merchandise'
    }
]

def create_categories():
    """Create categories if they don't exist"""
    created_count = 0
    
    for cat_data in categories:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'description': cat_data['description'],
                'slug': cat_data['slug']
            }
        )
        
        if created:
            print(f"✅ Created category: {category.name}")
            created_count += 1
        else:
            print(f"ℹ️  Category already exists: {category.name}")
    
    print(f"\n🎉 Successfully created {created_count} new categories!")
    print(f"📊 Total categories in database: {Category.objects.count()}")

if __name__ == '__main__':
    print("🚀 Creating categories for Somerset Shrimp Shack...")
    print("=" * 50)
    create_categories()
    print("=" * 50)
    print("✨ Done!")
