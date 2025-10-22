"""
Serializadores para la gestión de notificaciones.

Este módulo contiene los serializadores (serializers) utilizados para
serializar/deserializar datos de notificaciones entre la API REST y los modelos Django.

Serializadores:
    - NotificationSerializer: Serialización del modelo Notification
"""

from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Notification.

    Se utiliza para serializar notificaciones de usuarios del sistema.

    Campos de lectura:
        id (int): Identificador único de la notificación
        user (int): ID del usuario destinatario
        type (str): Tipo de notificación (ej: 'grade', 'enrollment')
        message (str): Contenido de la notificación
        created (datetime): Fecha y hora de creación (auto-asignado)
        read (bool): Indica si ha sido leída

    Campos de solo lectura:
        user: Se obtiene del usuario autenticado, no se puede cambiar
        created: Se establece automáticamente, no se puede modificar

    Campos modificables:
        read: El usuario puede marcar notificaciones como leídas
        message: Puede actualizarse si es necesario

    Nota:
        - Las notificaciones se crean automáticamente en el sistema
        - No se eliminan, solo se marcan como leídas
        - El usuario debe ser el propietario para modificar la notificación
    """
    class Meta:
        model = Notification
        fields = ["id","user","type","message","created","read"]
        read_only_fields = ["user","created"]
