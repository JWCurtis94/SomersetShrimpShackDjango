from django.db import migrations, models
import django.db.models.deletion

def forward_func(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    Category = apps.get_model('store', 'Category')
    
    # Create categories from existing values
    category_names = set(Product.objects.values_list('category', flat=True))
    category_dict = {}
    
    for name in category_names:
        if name:  # Only process non-empty names
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower().replace(' ', '-').replace('_', '-')}
            )
            category_dict[name] = category.id
    
    # Update each product with the correct category_id
    # The category_id field should already exist from the initial migration
    for product in Product.objects.all():
        if product.category and product.category in category_dict:
            product.category_id = category_dict[product.category]
            product.save(update_fields=['category_id'])

def reverse_func(apps, schema_editor):
    # Reverse operation - copy category names back from FK
    Product = apps.get_model('store', 'Product')
    
    for product in Product.objects.all():
        if product.category_id:
            try:
                category = product.category
                # This would require the old category field to exist
                # For now, just pass
                pass
            except:
                pass

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        # Run custom data migration
        migrations.RunPython(forward_func, reverse_func),
        
        # Change the field definition from CharField to ForeignKey
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products'),
        ),
    ]