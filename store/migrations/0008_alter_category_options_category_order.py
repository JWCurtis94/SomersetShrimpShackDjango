# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_category_image'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['order', 'name'], 'verbose_name_plural': 'Categories'},
        ),
        migrations.AddField(
            model_name='category',
            name='order',
            field=models.PositiveIntegerField(default=0, help_text='Order for displaying categories (lower numbers appear first)'),
        ),
    ]
