from rest_framework import permissions

from myapp.models import UserTypes


class IsNotCustomer(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type != UserTypes.CUSTOMER
