"""
Clases de permisos personalizados para control de acceso basado en roles.

Este módulo define las clases de permisos (Permission classes) utilizadas
para restringir acceso a los endpoints según el rol del usuario.

Clases:
    - IsAdmin: Permite acceso solo a usuarios autenticados con rol 'admin'
    - IsInstructor: Permite acceso solo a usuarios autenticados con rol 'instructor'
    - IsStudent: Permite acceso solo a usuarios autenticados con rol 'student'
"""

from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Verifica si el usuario está autenticado y tiene rol 'admin'.

    Uso:
        Se utiliza en endpoints que solo deben ser accesibles por administradores.
        Ejemplo: crear usuarios, crear materias, asignar profesores, ver estadísticas.

    Validación:
        1. user.is_authenticated: Usuario debe estar autenticado
        2. user.role: Usuario debe tener un rol asignado
        3. user.role.name == "admin": El rol debe ser 'admin'

    Returns:
        bool: True si el usuario es admin, False en caso contrario
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role
                and request.user.role.name == "admin")

class IsInstructor(BasePermission):
    """
    Verifica si el usuario está autenticado y tiene rol 'instructor'.

    Uso:
        Se utiliza en endpoints para profesores/instructores.
        Ejemplo: ver estudiantes, asignar calificaciones, cerrar materias.

    Validación:
        1. user.is_authenticated: Usuario debe estar autenticado
        2. user.role: Usuario debe tener un rol asignado
        3. user.role.name == "instructor": El rol debe ser 'instructor'

    Returns:
        bool: True si el usuario es instructor, False en caso contrario
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role
                and request.user.role.name == "instructor")

class IsStudent(BasePermission):
    """
    Verifica si el usuario está autenticado y tiene rol 'student'.

    Uso:
        Se utiliza en endpoints para estudiantes.
        Ejemplo: inscribirse en materias, ver calificaciones, consultar historial.

    Validación:
        1. user.is_authenticated: Usuario debe estar autenticado
        2. user.role: Usuario debe tener un rol asignado
        3. user.role.name == "student": El rol debe ser 'student'

    Returns:
        bool: True si el usuario es estudiante, False en caso contrario
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.role
                and request.user.role.name == "student")
