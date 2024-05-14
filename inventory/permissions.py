from rest_framework import permissions


class IsNotCustomer(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type != 'customer'


class CanChangeOrderStatusPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        # Check if the user is authenticated and is either an admin or belongs to the Customer Service group
        return request.user.is_authenticated and request.user.type != 'customer'


class IsAdminUserCustom(permissions.BasePermission):
    """
    Custom permission to only allow users with a specific 'is_admin' attribute to post.
    """

    def has_permission(self, request, view):

        if request.method == 'POST':
            return request.user.is_authenticated and request.user.type == 'A'

        return request.user.is_authenticated