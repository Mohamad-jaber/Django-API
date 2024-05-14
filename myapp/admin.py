from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address, Payment

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Address)
admin.site.register(Payment)
