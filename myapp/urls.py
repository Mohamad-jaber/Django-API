from django.urls import path
from . import views

urlpatterns = [
    path("users/", views.UserListCreate.as_view(), name="user-list"),
    path("customers/", views.CustomersListCreate.as_view(), name="customers-list"),
    path("employees/", views.EmployeesListCreate.as_view(), name="employees-list"),
    path('users/<int:pk>', views.UserEdit.as_view(), name='edit-profile'),
    path('users/login/', views.LoginView.as_view(), name='login'),
    path('users/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path("address/", views.AddressListCreate.as_view(), name="address-list"),
    path("address/<int:pk>/", views.AddressEdit.as_view(), name="address-list"),
    path('payments/', views.PaymentListCreateAPIView.as_view(), name='payment'),
]
