from base64 import b64encode

from django.conf import settings
from django.db import models
from myapp.models import CustomUser, Address
from django.utils.translation import gettext_lazy
import qrcode
from io import BytesIO


class OrderStatus(models.TextChoices):
    PENDING = 'P', gettext_lazy('Pending')
    APPROVED = 'A', gettext_lazy('Approved')
    DELIVERED = 'D', gettext_lazy('Delivered')
    CANCELLED = 'C', gettext_lazy('Cancelled')


class BottleStatus(models.TextChoices):
    AVAILABLE = 'A', gettext_lazy('Available')
    SOLD = 'S', gettext_lazy('Sold')
    DISCARDED = 'D', gettext_lazy('Discarded')


class Bottle(models.Model):
    bottleId = models.AutoField(primary_key=True)
    number_of_times_Sold = models.IntegerField(default=0)
    bottle_status = models.CharField(max_length=100, choices=BottleStatus.choices, default=BottleStatus.AVAILABLE)
    qr_code = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.qr_code:
            self.qr_code = self.generate_qr_code(self.bottleId)
            super().save()

    def generate_qr_code(self, data):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(data))
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        bio = BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        image_data = b64encode(bio.read()).decode('utf-8')  # Convert bytes to base64 string
        return image_data


class Orders(models.Model):
    order_date = models.DateTimeField(auto_now_add=True)
    order_quantity = models.PositiveIntegerField()
    order_status = models.CharField(max_length=100, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    order_notes = models.TextField(max_length=255, null=True, blank=True)
    delivery_date = models.DateField(null=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer',
        limit_choices_to={'type': 'customer'}
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='receiver',
        limit_choices_to={'type__in': ['admin', 'driver', 'customerService']},
        null=True
    )
    bottles = models.ManyToManyField(Bottle, through='BottleOrder')
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='Address')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.pk:  # Check if it's a new instance
            # Default price if no special price is set
            price_per_bottle = 20

            # Check if customer has a special bottle price
            if self.customer.specialBottlePrice > 0:
                price_per_bottle = self.customer.specialBottlePrice

            # Calculate the total price
            self.total_price = price_per_bottle * self.order_quantity

        super(Orders, self).save(*args, **kwargs)  # Call the real save method


class BottleOrder(models.Model):
    bottle = models.ForeignKey(Bottle, on_delete=models.CASCADE)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE)
    dateOfReturning = models.DateField(null=True)
