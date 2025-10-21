from django.db import models
from django.contrib.auth.models import AbstractUser

class Role(models.Model):
    """Modelo de roles del sistema"""
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
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True, related_name="users")
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student")
    max_credits_per_term = models.PositiveIntegerField(default=16)
class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="instructor")
    max_credits_per_term = models.PositiveIntegerField(default=20)
