from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("myapp.urls")),
    path("", include("inventory.urls")),
    path("", include('dashboard.urls')),
    path('i18n/', include('django.conf.urls.i18n')),

]
