"""
Modelos para gestión de notificaciones de usuarios.

Este módulo define:
- Notification: Representa una notificación enviada a un usuario del sistema
"""

from django.db import models
from accounts.models import User

class Notification(models.Model):
    """
    Representa una notificación en el sistema académico.

    Se crea automáticamente cuando ocurren eventos importantes, como cuando
    un profesor asigna una calificación a un estudiante.

    Atributos:
        user (ForeignKey): Usuario destinatario de la notificación
        type (CharField): Tipo de notificación (ej: 'grade', 'enrollment', etc.)
        message (TextField): Contenido descriptivo de la notificación
        created (DateTimeField): Fecha y hora de creación de la notificación (auto-asignado)
        read (BooleanField): Indica si el usuario ha leído la notificación (default: False)

    Ejemplos de notificaciones:
        - type='grade': Se dispara cuando un profesor asigna una calificación
            message='Grade 4.5 in Calculus I'
        - type='enrollment': Se dispara cuando hay cambios en inscripciones
        - type='status_change': Se dispara cuando cambia el estado de una inscripción

    Relaciones:
        - user: Relación muchos-a-uno con User (un usuario puede tener muchas notificaciones)
        - Cuando un usuario se elimina, se eliminan en cascada todas sus notificaciones

    Consideraciones de diseño:
        - Las notificaciones no se eliminan, solo se marcan como leídas
        - El campo 'created' se establece automáticamente y no puede modificarse
        - El campo 'type' es flexible para permitir diferentes tipos de notificaciones
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=50)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
