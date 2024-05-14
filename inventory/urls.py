from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.OrdersListCreateAPIView.as_view(), name='orders'),
    path('orders/customer/<int:customer_id>', views.OrdersListCreateAPIView.as_view(), name='orders_customer'),
    path('orders/<int:pk>', views.OrdersDetailAPIView.as_view(), name='orders_details'),
    path('orders/change-status/', views.ChangeOrderStatusAPIView.as_view(), name='change-order-status'),
    path('bottles/', views.BottleListCreateAPIView.as_view(), name='bottle-list-create'),
    path('bottles/add-bottles-to-order/', views.BottleOrderView.as_view(), name='add-bottles-to-order'),
    path('bottles/return-bottles/', views.ReturnBottlesView.as_view(), name='return-bottles'),

]
