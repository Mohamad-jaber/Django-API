# Generated by Django 4.2.11 on 2024-05-11 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_delete_userprofile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='specialBottlePrice',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
