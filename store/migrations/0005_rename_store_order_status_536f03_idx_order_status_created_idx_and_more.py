# Generated by Django 5.0.5 on 2025-05-21 20:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0004_merge_20250521_2117'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='order',
            new_name='order_status_created_idx',
            old_name='store_order_status_536f03_idx',
        ),
        migrations.RenameIndex(
            model_name='order',
            new_name='order_user_status_idx',
            old_name='store_order_user_id_c9744e_idx',
        ),
        migrations.RenameIndex(
            model_name='order',
            new_name='order_email_status_idx',
            old_name='store_order_email_ea22c8_idx',
        ),
        migrations.RenameIndex(
            model_name='orderitem',
            new_name='order_item_prod_idx',
            old_name='store_order_order_i_ec571c_idx',
        ),
        migrations.RenameIndex(
            model_name='product',
            new_name='prod_cat_avail_idx',
            old_name='store_produ_categor_b51135_idx',
        ),
        migrations.RenameIndex(
            model_name='product',
            new_name='prod_price_avail_idx',
            old_name='store_produ_price_7010f5_idx',
        ),
        migrations.RenameIndex(
            model_name='product',
            new_name='prod_feat_avail_idx',
            old_name='store_produ_feature_091f94_idx',
        ),
        migrations.RenameIndex(
            model_name='product',
            new_name='prod_size_cat_idx',
            old_name='store_produ_size_abd65a_idx',
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(db_column='category_id', on_delete=django.db.models.deletion.CASCADE, related_name='products', to='store.category'),
        ),
    ]
