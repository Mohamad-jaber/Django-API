from django.contrib import admin

from inventory.models import Bottle, Orders

# Register your models here.

admin.site.register(Bottle)
admin.site.register(Orders)
