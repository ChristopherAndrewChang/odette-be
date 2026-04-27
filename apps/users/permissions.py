from rest_framework.permissions import BasePermission


class IsSuperuser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser_role


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            request.user.ROLE_SUPERUSER,
            request.user.ROLE_ADMIN,
            request.user.ROLE_DJ,
            request.user.ROLE_CASHIER,
        )

# class IsDJ(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and request.user.role == User.ROLE_DJ