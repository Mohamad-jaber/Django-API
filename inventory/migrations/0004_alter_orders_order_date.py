# Generated by Django 4.2.11 on 2024-05-09 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_rename_customer_id_orders_customer_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orders',
            name='order_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]