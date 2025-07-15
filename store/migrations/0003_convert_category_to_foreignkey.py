from django.db import migrations, models
import django.db.models.deletion

def forward_func(apps, schema_editor):
    Product = apps.get_model('store', 'Product')
    Category = apps.get_model('store', 'Category')
    
    # Create categories from existing values
    category_names = set(Product.objects.values_list('category', flat=True))
    category_dict = {}
    
    for name in category_names:
        category, created = Category.objects.get_or_create(
            name=name,
            defaults={'slug': name.lower().replace(' ', '-')}
        )
        category_dict[name] = category.id
    
    # Add category_id field temporarily
    # We'll use raw SQL to avoid Django ORM's constraints
    db_alias = schema_editor.connection.alias
    schema_editor.execute(
        "ALTER TABLE store_product ADD COLUMN category_id integer"
    )
    
    # Update each product with the correct category_id
    for product in Product.objects.all():
        if product.category in category_dict:
            schema_editor.execute(
                f"UPDATE store_product SET category_id = {category_dict[product.category]} WHERE id = {product.id}"
            )

class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        # Run custom SQL
        migrations.RunPython(forward_func),
        
        # Change the field definition
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey('Category', on_delete=models.CASCADE, related_name='products'),
        ),
    ]