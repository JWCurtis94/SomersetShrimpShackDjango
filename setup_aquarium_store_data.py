#!/usr/bin/env python
"""
Setup script to populate Somerset Shrimp Shack with proper aquarium products
Corrected for aquarium shop business model (live aquarium animals, not restaurant food)
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from store.models import Category, Product
from decimal import Decimal

def create_aquarium_categories():
    """Create product categories for the aquarium shrimp shop"""
    categories_data = [
        {
            'name': 'Live Shrimp',
            'slug': 'live-shrimp',
            'description': 'Live freshwater aquarium shrimp - temperature controlled shipping required',
            'order': 1
        },
        {
            'name': 'Live Snails',
            'slug': 'live-snails',
            'description': 'Live aquarium snails for algae control and tank cleaning',
            'order': 2
        },
        {
            'name': 'Live Fish',
            'slug': 'live-fish',
            'description': 'Compatible tropical fish for shrimp tanks',
            'order': 3
        },
        {
            'name': 'Plants & Moss',
            'slug': 'plants-moss',
            'description': 'Live aquarium plants and moss for shrimp habitats',
            'order': 4
        },
        {
            'name': 'Shrimp Food',
            'slug': 'shrimp-food',
            'description': 'Specialized foods and supplements for aquarium shrimp',
            'order': 5
        },
        {
            'name': 'Equipment',
            'slug': 'equipment',
            'description': 'Tanks, filters, heaters and essential aquarium equipment',
            'order': 6
        },
        {
            'name': 'Water Care',
            'slug': 'water-care',
            'description': 'Water conditioners, minerals and testing supplies',
            'order': 7
        },
        {
            'name': 'Substrate & Decor',
            'slug': 'substrate-decor',
            'description': 'Aquarium substrates, rocks, driftwood and decorations',
            'order': 8
        }
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

def create_aquarium_products(categories):
    """Create aquarium products for each category"""
    cat_dict = {cat.slug: cat for cat in categories}
    
    products_data = [
        # Live Shrimp (£12 shipping - live animals)
        {'name': 'Cherry Shrimp (Neocaridina Red)', 'slug': 'cherry-shrimp-red', 'description': 'Beautiful red cherry shrimp, perfect for beginners. Hardy and easy to breed.', 'category': cat_dict['live-shrimp'], 'price': Decimal('3.99'), 'stock': 50},
        {'name': 'Blue Dream Shrimp', 'slug': 'blue-dream-shrimp', 'description': 'Stunning blue coloration, selectively bred from cherry shrimp line.', 'category': cat_dict['live-shrimp'], 'price': Decimal('4.99'), 'stock': 30},
        {'name': 'Crystal Red Shrimp (CRS)', 'slug': 'crystal-red-shrimp', 'description': 'Premium crystal red shrimp with beautiful red and white patterns.', 'category': cat_dict['live-shrimp'], 'price': Decimal('8.99'), 'stock': 25},
        {'name': 'Amano Shrimp', 'slug': 'amano-shrimp', 'description': 'Excellent algae eaters, larger than cherry shrimp. Great tank cleaners.', 'category': cat_dict['live-shrimp'], 'price': Decimal('5.99'), 'stock': 40},
        {'name': 'Ghost Shrimp', 'slug': 'ghost-shrimp', 'description': 'Transparent shrimp, perfect for beginners and great feeders for larger fish.', 'category': cat_dict['live-shrimp'], 'price': Decimal('1.99'), 'stock': 60},
        
        # Live Snails (£12 shipping - live animals)
        {'name': 'Nerite Snails', 'slug': 'nerite-snails', 'description': 'Best algae eating snails, will not breed in freshwater.', 'category': cat_dict['live-snails'], 'price': Decimal('3.49'), 'stock': 45},
        {'name': 'Mystery Snails', 'slug': 'mystery-snails', 'description': 'Colorful apple snails, great for community tanks.', 'category': cat_dict['live-snails'], 'price': Decimal('4.99'), 'stock': 35},
        {'name': 'Assassin Snails', 'slug': 'assassin-snails', 'description': 'Natural pest snail control, beautiful striped pattern.', 'category': cat_dict['live-snails'], 'price': Decimal('5.99'), 'stock': 20},
        
        # Live Fish (£12 shipping - live animals)  
        {'name': 'Otocinclus Catfish', 'slug': 'otocinclus-catfish', 'description': 'Small algae eating fish, perfect tank mates for shrimp.', 'category': cat_dict['live-fish'], 'price': Decimal('6.99'), 'stock': 25},
        {'name': 'Endler Guppies', 'slug': 'endler-guppies', 'description': 'Peaceful small fish compatible with adult shrimp.', 'category': cat_dict['live-fish'], 'price': Decimal('4.99'), 'stock': 30},
        
        # Plants & Moss (£6 shipping - non-live)
        {'name': 'Java Moss', 'slug': 'java-moss', 'description': 'Perfect hiding and breeding ground for baby shrimp.', 'category': cat_dict['plants-moss'], 'price': Decimal('7.99'), 'stock': 40},
        {'name': 'Marimo Moss Balls', 'slug': 'marimo-moss-balls', 'description': 'Low maintenance moss balls that shrimp love to graze on.', 'category': cat_dict['plants-moss'], 'price': Decimal('12.99'), 'stock': 35},
        {'name': 'Anubias Nana', 'slug': 'anubias-nana', 'description': 'Hardy aquarium plant perfect for shrimp tanks.', 'category': cat_dict['plants-moss'], 'price': Decimal('9.99'), 'stock': 30},
        
        # Shrimp Food (£6 shipping - non-live)
        {'name': 'Shrimp Pellets Premium', 'slug': 'shrimp-pellets-premium', 'description': 'High-quality sinking pellets specifically for freshwater shrimp.', 'category': cat_dict['shrimp-food'], 'price': Decimal('8.99'), 'stock': 50},
        {'name': 'Biofilm Booster', 'slug': 'biofilm-booster', 'description': 'Promotes beneficial biofilm growth that shrimp love to graze on.', 'category': cat_dict['shrimp-food'], 'price': Decimal('12.99'), 'stock': 25},
        {'name': 'Mineral Supplement Powder', 'slug': 'mineral-supplement-powder', 'description': 'Essential minerals for proper shrimp molting and health.', 'category': cat_dict['shrimp-food'], 'price': Decimal('15.99'), 'stock': 30},
        
        # Equipment (£6 shipping - non-live)
        {'name': 'Nano Aquarium Filter', 'slug': 'nano-aquarium-filter', 'description': 'Gentle filtration perfect for shrimp tanks, baby-safe.', 'category': cat_dict['equipment'], 'price': Decimal('24.99'), 'stock': 15},
        {'name': 'Aquarium Heater 25W', 'slug': 'aquarium-heater-25w', 'description': 'Adjustable heater for nano tanks, essential for tropical shrimp.', 'category': cat_dict['equipment'], 'price': Decimal('19.99'), 'stock': 20},
        {'name': 'LED Aquarium Light', 'slug': 'led-aquarium-light', 'description': 'Full spectrum LED lighting for plant and shrimp tanks.', 'category': cat_dict['equipment'], 'price': Decimal('34.99'), 'stock': 12},
        
        # Water Care (£6 shipping - non-live)
        {'name': 'Water Conditioner', 'slug': 'water-conditioner', 'description': 'Removes chlorine and makes tap water safe for shrimp.', 'category': cat_dict['water-care'], 'price': Decimal('7.99'), 'stock': 40},
        {'name': 'GH/KH Test Kit', 'slug': 'gh-kh-test-kit', 'description': 'Essential for monitoring water parameters for shrimp health.', 'category': cat_dict['water-care'], 'price': Decimal('16.99'), 'stock': 25},
        
        # Substrate & Decor (£6 shipping - non-live)
        {'name': 'Active Aquarium Substrate', 'slug': 'active-aquarium-substrate', 'description': 'pH buffering substrate ideal for crystal and bee shrimp.', 'category': cat_dict['substrate-decor'], 'price': Decimal('22.99'), 'stock': 18},
        {'name': 'Cholla Wood Pieces', 'slug': 'cholla-wood-pieces', 'description': 'Natural driftwood that promotes biofilm growth for shrimp feeding.', 'category': cat_dict['substrate-decor'], 'price': Decimal('11.99'), 'stock': 35},
        {'name': 'Ceramic Breeding Tubes', 'slug': 'ceramic-breeding-tubes', 'description': 'Perfect hiding spots for shrimp and breeding caves.', 'category': cat_dict['substrate-decor'], 'price': Decimal('8.99'), 'stock': 30}
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
            # Determine shipping type
            shipping_type = "£12 (Live)" if product.is_shrimp_product else "£6 (Standard)"
            print(f"✓ Created product: {product.name} - £{product.price} (Stock: {product.stock}) - Shipping: {shipping_type}")
        else:
            print(f"• Product already exists: {product.name}")
        created_products.append(product)
    
    return created_products

def main():
    print("Somerset Shrimp Shack - Aquarium Store Setup")
    print("=" * 45)
    
    # Clear existing restaurant data
    print("\n🗑️  Clearing old restaurant data...")
    Product.objects.all().delete()
    Category.objects.all().delete()
    print("✓ Cleared old data")
    
    print("\n📁 Creating Aquarium Categories...")
    categories = create_aquarium_categories()
    
    print(f"\n🐠 Creating Aquarium Products...")
    products = create_aquarium_products(categories)
    
    print(f"\n✅ Aquarium Store Setup Complete!")
    print(f"Created {len(categories)} categories and {len(products)} products")
    
    # Summary with shipping breakdown
    live_products = [p for p in products if p.is_shrimp_product]
    non_live_products = [p for p in products if not p.is_shrimp_product]
    
    total_stock = sum(p.stock for p in products)
    print(f"\n📊 Summary:")
    print(f"• Categories: {Category.objects.count()}")
    print(f"• Total Products: {Product.objects.count()}")
    print(f"  - Live Animals (£12 shipping): {len(live_products)}")
    print(f"  - Non-Live Items (£6 shipping): {len(non_live_products)}")
    print(f"• Total Stock Items: {total_stock}")
    print(f"• Stock Value: £{sum(p.price * p.stock for p in products):.2f}")
    
    # Show shipping breakdown
    print(f"\n🚚 Shipping Cost Verification:")
    print(f"Live Animals (£12 shipping):")
    for product in live_products:
        print(f"  • {product.name} - {product.category.name}")
    
    print(f"\nNon-Live Items (£6 shipping):")
    for product in non_live_products:
        print(f"  • {product.name} - {product.category.name}")

if __name__ == '__main__':
    main()
