# Generated by Django 5.1.6 on 2025-03-06 19:53

import django.core.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_alter_product_created_at'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ['-created_at'], 'verbose_name': 'Order', 'verbose_name_plural': 'Orders'},
        ),
        migrations.AlterModelOptions(
            name='orderitem',
            options={'verbose_name': 'Order Item', 'verbose_name_plural': 'Order Items'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['-created_at'], 'verbose_name': 'Product', 'verbose_name_plural': 'Products'},
        ),
        migrations.AddField(
            model_name='order',
            name='order_reference',
            field=models.CharField(blank=True, max_length=100, unique=True),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='size',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='featured',
            field=models.BooleanField(default=False, help_text='Feature this product on the homepage'),
        ),
        migrations.AddField(
            model_name='product',
            name='size',
            field=models.CharField(blank=True, choices=[('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='notes',
            field=models.TextField(blank=True, help_text='Any special instructions or notes for this order'),
        ),
        migrations.AlterField(
            model_name='order',
            name='shipping_country',
            field=models.CharField(blank=True, default='United Kingdom', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='shipping_phone',
            field=models.CharField(blank=True, max_length=20, null=True, validators=[django.core.validators.RegexValidator('^\\+?\\d{7,15}$', 'Enter a valid phone number.')]),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], db_index=True, default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='stripe_checkout_id',
            field=models.CharField(db_index=True, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='tracking_number',
            field=models.CharField(blank=True, help_text='Shipping carrier tracking number', max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='stock',
            field=models.IntegerField(default=0),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['email', 'status'], name='store_order_email_ea22c8_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['featured', 'available'], name='store_produ_feature_091f94_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['size', 'category'], name='store_produ_size_abd65a_idx'),
        ),
    ]
