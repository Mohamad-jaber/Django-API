# Generated by Django 4.2.11 on 2024-05-12 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_alter_orders_order_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='bottle',
            name='qr_code',
            field=models.BinaryField(blank=True, null=True),
        ),
    ]