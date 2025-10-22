"""
Vistas para gestión de usuarios y roles.

Este módulo proporciona endpoints REST para:
- Listar y recuperar usuarios
- Crear nuevos usuarios del sistema
- Asignar roles a usuarios
- Obtener estadísticas académicas del sistema
"""

from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsAdmin
from drf_yasg.utils import swagger_auto_schema
from .models import User
from .serializers import UserSerializer, CreateUserSerializer, AdminStatisticsSerializer, AssignRoleSerializer
from .services import assign_role, get_admin_statistics

class UserViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    """
    ViewSet para gestión de usuarios del sistema académico.

    Endpoints:
        GET /users/ - Listar todos los usuarios (requiere autenticación)
        GET /users/{id}/ - Obtener detalle de un usuario (requiere autenticación)
        POST /users/create_user/ - Crear un nuevo usuario (requiere autenticación y rol admin)
        POST /users/{id}/assign_role/ - Asignar rol a un usuario (requiere autenticación y rol admin)
        GET /users/statistics/ - Obtener estadísticas del sistema (requiere autenticación y rol admin)
    """
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsAdmin])
    def create_user(self, request):
        """
        Crea un nuevo usuario en el sistema.

        Args:
            request: Solicitud HTTP con datos del usuario en el body:
                - username (str): Nombre único de usuario
                - email (str): Correo electrónico del usuario
                - password (str): Contraseña del usuario
                - first_name (str, opcional): Primer nombre
                - last_name (str, opcional): Apellido
                - role (int): ID del rol a asignar (1=admin, 2=instructor, 3=student)

        Returns:
            Response: Objeto del usuario creado con datos completos y status HTTP 201

        Nota:
            Si se asigna el rol 'student', se crea automáticamente un perfil Student
            Si se asigna el rol 'instructor', se crea automáticamente un perfil Instructor
        """
        s = CreateUserSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        u = s.save()
        return Response(UserSerializer(u).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(request_body=AssignRoleSerializer, responses={200: UserSerializer})
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdmin])
    def assign_role(self, request, pk=None):
        """
        Asigna un rol a un usuario existente.

        Args:
            request: Solicitud HTTP con datos en el body:
                - role (str): Nombre del rol ('admin', 'instructor', o 'student')
            pk: ID del usuario al que se asignará el rol

        Returns:
            Response: Objeto del usuario actualizado con su nuevo rol

        Comportamiento:
            - Si se asigna rol 'student', crea automáticamente perfil Student si no existe
            - Si se asigna rol 'instructor', crea automáticamente perfil Instructor si no existe
            - Solo administradores pueden asignar roles

        Raises:
            Http404: Si el usuario no existe
            Http400: Si el rol especificado no existe
        """
        role = request.data.get("role")
        u = assign_role(pk, role)
        return Response(UserSerializer(u).data)

    @swagger_auto_schema(request_body=AssignRoleSerializer, responses={200: UserSerializer})
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdmin])
    def change_role(self, request, pk=None):
        """
        Cambia el rol de un usuario que ya tiene uno asignado.

        Args:
            request: Solicitud HTTP con datos en el body:
                - role (str): Nombre del nuevo rol ('admin', 'instructor', o 'student')
            pk: ID del usuario cuyo rol se cambiará

        Returns:
            Response: Objeto del usuario actualizado con su nuevo rol

        Comportamiento:
            - Similar a assign_role pero se utiliza cuando el usuario ya tiene un rol
            - Si se cambia a rol 'student', crea automáticamente perfil Student si no existe
            - Si se cambia a rol 'instructor', crea automáticamente perfil Instructor si no existe
            - Solo administradores pueden cambiar roles

        Raises:
            Http404: Si el usuario no existe
            Http400: Si el rol especificado no existe
        """
        role = request.data.get("role")
        u = assign_role(pk, role)
        return Response(UserSerializer(u).data)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdmin])
    def statistics(self, request):
        """
        Retorna estadísticas completas del sistema académico.

        Solo accesible para administradores.

        Returns:
            Response: Diccionario con estadísticas que incluye:
                - users: Cantidad de usuarios por rol y estado de actividad
                - subjects: Información sobre materias y asignación de profesores
                - enrollments: Estado de inscripciones (enrolled, approved, failed, closed)
                - academic_performance: Tasas de aprobación, promedio general, GPA
                - grade_distribution: Distribución de calificaciones por rangos
                - professors_with_assignments: Total de profesores con materias asignadas

        Cálculos incluidos:
            - Conteo de usuarios por rol (admin, instructor, student)
            - Estudiantes activos vs inactivos
            - Inscripciones agrupadas por estado
            - Tasas de aprobación/reprobación
            - Promedios de calificaciones
        """
        stats = get_admin_statistics()
        serializer = AdminStatisticsSerializer(stats)
        return Response(serializer.data)
