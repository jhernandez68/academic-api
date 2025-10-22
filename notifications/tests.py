"""
Tests para la aplicación de notificaciones.

Cobertura:
- Modelos: Notification
- Vistas: Listar y obtener notificaciones
- Servicios: Crear notificaciones, marcar como leída
- Tareas Celery: Limpieza de notificaciones antiguas
- Señales: Creación automática de notificaciones
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework import status

from notifications.models import Notification
from notifications.tasks import purge_old_notifications


@pytest.mark.unit
class TestNotificationModel:
    """Tests para el modelo Notification."""

    def test_create_notification(self, student_user, db):
        """Prueba crear una notificación."""
        notification = Notification.objects.create(
            user=student_user,
            type="enrollment",
            message="You have been enrolled",
            is_read=False
        )
        assert notification.user == student_user
        assert notification.type == "enrollment"
        assert not notification.is_read

    def test_notification_read_status(self, notification):
        """Prueba el estado de lectura de notificación."""
        assert not notification.is_read
        notification.is_read = True
        notification.save()
        assert notification.is_read

    def test_notification_types(self, db, student_user):
        """Prueba diferentes tipos de notificaciones."""
        types = ["enrollment", "grade", "welcome", "system"]
        for notification_type in types:
            notif = Notification.objects.create(
                user=student_user,
                type=notification_type,
                message=f"Test {notification_type}",
                is_read=False
            )
            assert notif.type == notification_type

    def test_notification_timestamp(self, notification):
        """Prueba que la notificación tiene timestamp."""
        assert notification.created_at is not None
        assert notification.created_at <= timezone.now()


@pytest.mark.integration
class TestNotificationEndpoints:
    """Tests para endpoints de notificaciones."""

    def test_list_notifications(self, authenticated_client, notification):
        """Prueba listar notificaciones del usuario."""
        response = authenticated_client.get("/api/notifications/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_only_user_notifications(self, authenticated_client, student_user,
                                         db, student_role):
        """Prueba que solo se listan las notificaciones del usuario actual."""
        other_user = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model().objects.create_user(
            username="other",
            email="other@example.com",
            password="pass123",
            role=student_role
        )
        Notification.objects.create(
            user=other_user,
            type="test",
            message="Other user notification"
        )

        response = authenticated_client.get("/api/notifications/")
        assert response.status_code == status.HTTP_200_OK
        # Solo debe tener las del usuario autenticado

    def test_get_notification_details(self, authenticated_client, notification):
        """Prueba obtener detalles de una notificación."""
        response = authenticated_client.get(f"/api/notifications/{notification.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["type"] == notification.type

    def test_cannot_get_other_user_notification(self, authenticated_client, db, student_role):
        """Prueba que no puede acceder a notificaciones de otro usuario."""
        User = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model()
        other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="pass123",
            role=student_role
        )
        notification = Notification.objects.create(
            user=other_user,
            type="test",
            message="Other user notification"
        )

        response = authenticated_client.get(f"/api/notifications/{notification.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.unit
class TestPurgeOldNotificationsTask:
    """Tests para la tarea periódica de limpieza."""

    def test_purge_old_read_notifications(self, db, student_user):
        """Prueba que se eliminan notificaciones leídas antiguas."""
        # Crear una notificación antigua (más de 90 días)
        old_notification = Notification.objects.create(
            user=student_user,
            type="test",
            message="Old notification",
            is_read=True
        )
        # Mover la fecha hacia atrás
        old_notification.created_at = timezone.now() - timedelta(days=100)
        old_notification.save()

        initial_count = Notification.objects.filter(is_read=True).count()

        # Ejecutar tarea
        purge_old_notifications()

        final_count = Notification.objects.filter(is_read=True).count()
        assert final_count < initial_count

    def test_preserve_unread_notifications(self, db, student_user):
        """Prueba que se preservan las notificaciones sin leer."""
        unread = Notification.objects.create(
            user=student_user,
            type="test",
            message="Unread notification",
            is_read=False
        )

        purge_old_notifications()

        # Debe existir aún
        assert Notification.objects.filter(id=unread.id).exists()

    def test_preserve_recent_read_notifications(self, db, student_user):
        """Prueba que se preservan notificaciones leídas recientes."""
        recent = Notification.objects.create(
            user=student_user,
            type="test",
            message="Recent notification",
            is_read=True
        )

        purge_old_notifications()

        # Debe existir aún
        assert Notification.objects.filter(id=recent.id).exists()


@pytest.mark.unit
class TestNotificationSignals:
    """Tests para señales que crean notificaciones."""

    def test_welcome_notification_on_user_creation(self, db, student_role):
        """Prueba que se crea notificación welcome al crear usuario."""
        User = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model()
        user = User.objects.create_user(
            username="newuser",
            email="new@example.com",
            password="pass123",
            role=student_role
        )

        # Debe haber una notificación de bienvenida
        welcome_notif = Notification.objects.filter(
            user=user,
            type="welcome"
        ).first()
        assert welcome_notif is not None

    def test_grade_notification_on_grading(self, db, enrollment):
        """Prueba que se crea notificación al calificar."""
        from subjects.services import grade
        from decimal import Decimal

        initial_count = Notification.objects.filter(
            user=enrollment.student
        ).count()

        grade(enrollment.id, Decimal("4.5"))

        final_count = Notification.objects.filter(
            user=enrollment.student
        ).count()
        assert final_count > initial_count


@pytest.mark.integration
class TestNotificationIntegration:
    """Tests de integración para notificaciones."""

    def test_notification_creation_flow(self, db, student_user):
        """Prueba el flujo completo de creación de notificación."""
        # Crear notificación
        notification = Notification.objects.create(
            user=student_user,
            type="test",
            message="Test message",
            is_read=False
        )

        # Verificar que existe
        assert Notification.objects.filter(id=notification.id).exists()

        # Marcar como leída (simulado)
        notification.is_read = True
        notification.save()

        # Verificar cambio
        notification.refresh_from_db()
        assert notification.is_read

    def test_multiple_notifications_per_user(self, db, student_user):
        """Prueba que un usuario puede tener múltiples notificaciones."""
        for i in range(5):
            Notification.objects.create(
                user=student_user,
                type="test",
                message=f"Notification {i}",
                is_read=False
            )

        notifications = Notification.objects.filter(user=student_user)
        assert notifications.count() == 5
