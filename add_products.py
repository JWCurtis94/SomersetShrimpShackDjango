# add_products.py
from decimal import Decimal
from django.utils.text import slugify

# Product data organized by category
products = [
    # Neocaridina
    {"name": "Red Cherry Shrimp - Small", "category": "neocaridina", "price": Decimal("2.50"), "size": "small", "description": "Popular bright red freshwater shrimp, perfect for beginners.", "stock": 30},
    {"name": "Red Cherry Shrimp - Medium", "category": "neocaridina", "price": Decimal("3.00"), "size": "medium", "description": "Popular bright red freshwater shrimp, perfect for beginners.", "stock": 25},
    {"name": "Red Cherry Shrimp - Large", "category": "neocaridina", "price": Decimal("3.50"), "size": "large", "description": "Popular bright red freshwater shrimp, perfect for beginners.", "stock": 20},
    {"name": "Yellow Fire Shrimp", "category": "neocaridina", "price": Decimal("3.50"), "description": "Vibrant yellow variety of Neocaridina shrimp.", "stock": 25},
    {"name": "Green Jade Shrimp", "category": "neocaridina", "price": Decimal("3.50"), "description": "Beautiful green variety of Neocaridina shrimp.", "stock": 25},
    {"name": "Blue Dream Shrimp", "category": "neocaridina", "price": Decimal("3.50"), "description": "Striking blue variety of Neocaridina shrimp.", "stock": 25},
    
    # Caridina
    {"name": "Pure Red Line (PRL) Shrimp", "category": "caridina", "price": Decimal("7.50"), "description": "High-grade crystal red shrimp with deep coloration.", "stock": 15},
    {"name": "Pinto Crystal Red Shrimp", "category": "caridina", "price": Decimal("7.50"), "description": "Unique patterned crystal red shrimp.", "stock": 15},
    {"name": "Black Galaxy Fishbone Shrimp", "category": "caridina", "price": Decimal("10.00"), "description": "Rare black shrimp with distinctive white markings.", "stock": 12},
    {"name": "Boa Shrimp", "category": "caridina", "price": Decimal("28.00"), "description": "Highly sought-after premium shrimp with unique pattern.", "stock": 8},
    {"name": "Shadow Panda Shrimp", "category": "caridina", "price": Decimal("8.00"), "description": "Beautiful black and white panda shrimp variant.", "stock": 15},
    {"name": "Blue Steel Shrimp", "category": "caridina", "price": Decimal("5.00"), "description": "Metallic blue caridina variety.", "stock": 20},
    {"name": "Blue Mosura Shrimp", "category": "caridina", "price": Decimal("6.00"), "description": "Blue shrimp with distinctive mosura pattern.", "stock": 18},
    {"name": "Blue Bolt Shrimp - Small", "category": "caridina", "price": Decimal("6.00"), "size": "small", "description": "Popular blue caridina variety with bold coloration.", "stock": 20},
    {"name": "Blue Bolt Shrimp - Large", "category": "caridina", "price": Decimal("9.00"), "size": "large", "description": "Popular blue caridina variety with bold coloration.", "stock": 15},
    
    # Floating Plants
    {"name": "Amazon Frogbit", "category": "floating_plants", "price": Decimal("3.00"), "description": "Easy floating plant with large round leaves.", "stock": 30},
    {"name": "Red Root Floater", "category": "floating_plants", "price": Decimal("3.00"), "description": "Beautiful floating plant with red roots and small leaves.", "stock": 30},
    
    # Stem Plants
    {"name": "Ludwigia Palustris", "category": "stem_plants", "price": Decimal("3.50"), "description": "Reddish stem plant that adds color to your aquarium.", "stock": 25},
    {"name": "Cabomba Furcata", "category": "stem_plants", "price": Decimal("3.50"), "description": "Delicate purple/red feathery stem plant.", "stock": 25},
    {"name": "Elodea Densa", "category": "stem_plants", "price": Decimal("3.00"), "description": "Fast-growing oxygenating plant, perfect for new tanks.", "stock": 30},
    {"name": "Bacopa Mini", "category": "stem_plants", "price": Decimal("3.50"), "description": "Compact stem plant with small round leaves.", "stock": 25},
    {"name": "Rotala Blood Red", "category": "stem_plants", "price": Decimal("3.50"), "description": "Vibrant red stem plant for adding color highlights.", "stock": 25},
    
    # Rosette Plants
    {"name": "Echinodorus Red Devil", "category": "rosette_plants", "price": Decimal("4.50"), "description": "Bold red sword plant with striking foliage.", "stock": 20},
    {"name": "Echinodorus Red Diamond", "category": "rosette_plants", "price": Decimal("4.50"), "description": "Red-tinted sword plant with diamond-shaped leaves.", "stock": 20},
    
    # Botanicals
    {"name": "Cattapa Leaves", "category": "botanicals", "price": Decimal("4.00"), "description": "Natural leaves that release tannins beneficial for shrimp.", "stock": 35},
    {"name": "Alder Cones", "category": "botanicals", "price": Decimal("2.50"), "description": "Natural cones that help lower pH and release beneficial compounds.", "stock": 40},
    
    # Food
    {"name": "Shrimp Scran", "category": "food", "price": Decimal("4.00"), "description": "Premium food blend specially formulated for shrimp health and color.", "stock": 30},
    
    # Merchandise
    {"name": "Somerset Shrimp Shack Mug", "category": "merchandise", "price": Decimal("9.00"), "description": "Ceramic mug featuring our logo and shrimp designs.", "stock": 15},
    {"name": "Shrimp Enthusiast T-Shirt", "category": "merchandise", "price": Decimal("18.00"), "description": "Comfortable cotton t-shirt with artistic shrimp design.", "stock": 12},
    {"name": "Somerset Shrimp Shack Hoodie", "category": "merchandise", "price": Decimal("28.00"), "description": "Cozy hoodie featuring our logo, perfect for chilly days.", "stock": 10},
]

def run():
    from store.models import Product
    
    # Counter for created products
    created_count = 0
    
    for product_data in products:
        # Generate slug if not provided
        if 'slug' not in product_data:
            product_data['slug'] = slugify(product_data['name'])
            
        # Set defaults if not specified
        if 'available' not in product_data:
            product_data['available'] = True
        if 'featured' not in product_data:
            product_data['featured'] = False
        if 'size' not in product_data:
            product_data['size'] = None
            
        # Set meta description if not provided
        if 'meta_description' not in product_data:
            product_data['meta_description'] = f"Buy {product_data['name']} - Somerset Shrimp Shack"
            
        try:
            # Check if product with same name already exists
            existing = Product.objects.filter(name=product_data['name']).first()
            if existing:
                print(f"Product '{product_data['name']}' already exists, skipping.")
                continue
                
            # Create the product
            product = Product.objects.create(**product_data)
            print(f"Created: {product.name} (£{product.price})")
            created_count += 1
            
        except Exception as e:
            print(f"Error creating {product_data['name']}: {str(e)}")
    
    print(f"\nCreated {created_count} new products successfully!")

# Add this line at the end
if __name__ == "__main__":
    run()