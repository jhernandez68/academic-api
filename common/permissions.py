from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role
                and request.user.role.name == "admin")

class IsInstructor(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role
                and request.user.role.name == "instructor")

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role
                and request.user.role.name == "student")
