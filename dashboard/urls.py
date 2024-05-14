from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.IndexView.as_view(), name='dashboard'),
    path('dashboard/payment', views.PaymentListView.as_view(), name='payment'),
    path('dashboard/orders', views.OrderListView.as_view(), name='orders'),
    path('dashboard/bottles', views.BottlesListView.as_view(), name='bottles'),
]
