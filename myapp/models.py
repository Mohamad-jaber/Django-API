from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django.conf import settings
from rest_framework.exceptions import ValidationError


class UserTypes(models.TextChoices):
    Admin = 'A', 'Admin'
    CUSTOMER = 'C', 'Customer'
    DRIVER = 'D', 'Driver'
    CUSTOMER_SERVICE = 'CS', 'CustomerService'


class CustomUser(AbstractUser):
    type = models.CharField(max_length=100, choices=UserTypes.choices)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)  # Make email unique
    specialBottlePrice = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'


class Address(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')

    def clean(self):
        super().clean()
        if self.user.type != 'customer':
            raise ValidationError("Only customers can have addresses.")


class Payment(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments_as_customer',
        limit_choices_to={'type': 'customer'}
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments_as_receiver',
        limit_choices_to={'type__in': ['admin', 'driver', 'customerService']},
        null=True
    )
