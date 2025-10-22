"""
Modelos de autenticación y gestión de usuarios.

Este módulo define:
- Role: Define los roles del sistema (admin, instructor, student)
- User: Extiende AbstractUser de Django con campo de rol
- Student: Perfil específico de estudiante con límite de créditos
- Instructor: Perfil específico de profesor con límite de créditos
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.Model):
    """
    Define los roles disponibles en el sistema académico.

    Atributos:
        name (CharField): Identificador único del rol (admin, instructor, student)
        display_name (CharField): Nombre legible del rol para mostrar en la interfaz
        description (TextField): Descripción detallada del rol y sus permisos
        created_at (DateTimeField): Fecha de creación del rol
        updated_at (DateTimeField): Última fecha de actualización del rol
    """
    ROLE_TYPES = [
        ("admin", "Administrador"),
        ("instructor", "Instructor"),
        ("student", "Estudiante"),
    ]

    name = models.CharField(max_length=20, choices=ROLE_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.display_name


class User(AbstractUser):
    """
    Modelo de usuario extendido de Django.

    Extiende AbstractUser añadiendo:
        role (ForeignKey): Referencia al rol del usuario (puede ser null para usuarios sin rol asignado)
    """
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True, related_name="users")


class Student(models.Model):
    """
    Perfil específico de estudiante.

    Se crea automáticamente cuando un usuario es asignado al rol 'student'.

    Atributos:
        user (OneToOneField): Referencia única al usuario estudiante
        max_credits_per_term (PositiveIntegerField): Máximo de créditos que puede inscribir por semestre (default: 16)
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student")
    max_credits_per_term = models.PositiveIntegerField(default=16)


class Instructor(models.Model):
    """
    Perfil específico de profesor/instructor.

    Se crea automáticamente cuando un usuario es asignado al rol 'instructor'.

    Atributos:
        user (OneToOneField): Referencia única al usuario instructor
        max_credits_per_term (PositiveIntegerField): Máximo de créditos que puede enseñar por semestre (default: 20)
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="instructor")
    max_credits_per_term = models.PositiveIntegerField(default=20)
