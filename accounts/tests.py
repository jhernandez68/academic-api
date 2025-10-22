"""
Tests para la aplicación de cuentas (autenticación y usuarios).

Cobertura:
- Modelos: Role, User, Student, Instructor
- Vistas: Crear usuarios, asignar roles, obtener estadísticas
- Servicios: assign_role, get_admin_statistics
- Permisos: IsAdmin, IsStudent, IsInstructor
- Signals: Creación automática de perfiles
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Role, Student, Instructor
from accounts.services import assign_role, get_admin_statistics
from common.permissions import IsAdmin, IsStudent, IsInstructor
from subjects.models import Subject, Enrollment

User = get_user_model()


# ============================================================================
# TESTS DE MODELOS
# ============================================================================

@pytest.mark.unit
class TestRoleModel:
    """Tests para el modelo Role."""

    def test_create_role(self, db):
        """Prueba crear un rol."""
        role, created = Role.objects.get_or_create(
            name="custom_role",
            defaults={
                "display_name": "Custom Role",
                "description": "A custom role for testing"
            }
        )
        assert role.name == "custom_role"
        assert role.display_name == "Custom Role"

    def test_role_string_representation(self, admin_role):
        """Prueba la representación en string del rol."""
        assert str(admin_role) == "Administrador"

    def test_role_choices(self, db):
        """Prueba que los roles tienen opciones válidas."""
        valid_names = ["admin", "instructor", "student"]
        role_choices = [choice[0] for choice in Role.ROLE_TYPES]
        assert all(name in role_choices for name in valid_names)


@pytest.mark.unit
class TestUserModel:
    """Tests para el modelo User."""

    def test_create_user(self, student_role, db):
        """Prueba crear un usuario."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role=student_role
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == student_role

    def test_user_password_encrypted(self, student_user):
        """Prueba que la contraseña está encriptada."""
        assert student_user.check_password("student123")
        assert student_user.password != "student123"

    def test_user_without_role(self, db):
        """Prueba crear un usuario sin rol."""
        user = User.objects.create_user(
            username="norole",
            email="norole@example.com",
            password="pass123"
        )
        assert user.role is None


@pytest.mark.unit
class TestStudentProfile:
    """Tests para el perfil de estudiante."""

    def test_student_profile_created_on_signal(self, student_user):
        """Prueba que el perfil de estudiante se crea automáticamente."""
        assert hasattr(student_user, "student")
        assert student_user.student.max_credits_per_term == 16

    def test_student_profile_default_credits(self, student_user):
        """Prueba que el máximo de créditos por defecto es 16."""
        assert student_user.student.max_credits_per_term == 16

    def test_student_profile_custom_credits(self, db, student_role):
        """Prueba establecer créditos personalizados."""
        user = User.objects.create_user(
            username="customstudent",
            email="custom@example.com",
            password="pass123",
            role=student_role
        )
        user.student.max_credits_per_term = 20
        user.student.save()
        assert user.student.max_credits_per_term == 20


@pytest.mark.unit
class TestInstructorProfile:
    """Tests para el perfil de instructor."""

    def test_instructor_profile_created_on_signal(self, instructor_user):
        """Prueba que el perfil de instructor se crea automáticamente."""
        assert hasattr(instructor_user, "instructor")
        assert instructor_user.instructor.max_credits_per_term == 20

    def test_instructor_profile_default_credits(self, instructor_user):
        """Prueba que el máximo de créditos por defecto es 20."""
        assert instructor_user.instructor.max_credits_per_term == 20


# ============================================================================
# TESTS DE SERVICIOS
# ============================================================================

@pytest.mark.unit
class TestAssignRoleService:
    """Tests para el servicio assign_role."""

    def test_assign_student_role_creates_profile(self, db, student_role):
        """Prueba que asignar rol student crea el perfil."""
        user = User.objects.create_user(
            username="newuser",
            email="newuser@example.com",
            password="pass123"
        )
        assert not hasattr(user, "student")

        assign_role(user.id, "student")
        user.refresh_from_db()

        assert user.role.name == "student"
        assert hasattr(user, "student")

    def test_assign_instructor_role_creates_profile(self, db, instructor_role):
        """Prueba que asignar rol instructor crea el perfil."""
        user = User.objects.create_user(
            username="newinstruct",
            email="newinstruct@example.com",
            password="pass123"
        )

        assign_role(user.id, "instructor")
        user.refresh_from_db()

        assert user.role.name == "instructor"
        assert hasattr(user, "instructor")

    def test_assign_admin_role(self, db, admin_role):
        """Prueba asignar rol admin."""
        user = User.objects.create_user(
            username="newadmin",
            email="newadmin@example.com",
            password="pass123"
        )

        assign_role(user.id, "admin")
        user.refresh_from_db()

        assert user.role.name == "admin"


@pytest.mark.unit
class TestGetAdminStatistics:
    """Tests para el servicio get_admin_statistics."""

    def test_statistics_structure(self, complete_scenario):
        """Prueba que las estadísticas tienen la estructura correcta."""
        stats = get_admin_statistics()

        assert "total_users" in stats
        assert "total_subjects" in stats
        assert "total_enrollments" in stats
        assert "academic_performance" in stats
        assert "grade_distribution" in stats
        assert "professors_with_assignments" in stats

    def test_total_users_count(self, admin_user, instructor_user, student_user):
        """Prueba que se cuentan correctamente los usuarios."""
        stats = get_admin_statistics()
        assert stats["total_users"] >= 3

    def test_total_subjects_count(self, complete_scenario):
        """Prueba que se cuentan correctamente las materias."""
        stats = get_admin_statistics()
        assert stats["total_subjects"] >= 1

    def test_total_enrollments_count(self, complete_scenario):
        """Prueba que se cuentan correctamente las inscripciones."""
        stats = get_admin_statistics()
        assert stats["total_enrollments"] >= 1

    def test_grade_distribution(self, db, student_user, subject_without_prerequisites):
        """Prueba la distribución de calificaciones."""
        # Crear varias inscripciones con diferentes calificaciones
        Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="approved",
            grade=Decimal("5.0")
        )

        stats = get_admin_statistics()
        assert "grade_distribution" in stats


# ============================================================================
# TESTS DE PERMISOS
# ============================================================================

@pytest.mark.permission
class TestPermissions:
    """Tests para los permisos de rol."""

    def test_is_admin_permission(self, admin_user):
        """Prueba el permiso IsAdmin."""
        permission = IsAdmin()
        mock_request = type('Request', (), {'user': admin_user})()
        assert permission.has_permission(mock_request, None)

    def test_is_admin_permission_fails_for_student(self, student_user):
        """Prueba que IsAdmin falla para estudiantes."""
        permission = IsAdmin()
        mock_request = type('Request', (), {'user': student_user})()
        assert not permission.has_permission(mock_request, None)

    def test_is_student_permission(self, student_user):
        """Prueba el permiso IsStudent."""
        permission = IsStudent()
        mock_request = type('Request', (), {'user': student_user})()
        assert permission.has_permission(mock_request, None)

    def test_is_instructor_permission(self, instructor_user):
        """Prueba el permiso IsInstructor."""
        permission = IsInstructor()
        mock_request = type('Request', (), {'user': instructor_user})()
        assert permission.has_permission(mock_request, None)

    def test_is_instructor_permission_fails_for_student(self, student_user):
        """Prueba que IsInstructor falla para estudiantes."""
        permission = IsInstructor()
        mock_request = type('Request', (), {'user': student_user})()
        assert not permission.has_permission(mock_request, None)


# ============================================================================
# TESTS DE VISTAS (API ENDPOINTS)
# ============================================================================

@pytest.mark.integration
class TestAuthenticationEndpoints:
    """Tests para los endpoints de autenticación."""

    def test_obtain_token(self, api_client, student_user):
        """Prueba obtener token JWT."""
        response = api_client.post("/api/auth/token/", {
            "username": "student",
            "password": "student123"
        })
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_obtain_token_invalid_password(self, api_client, student_user):
        """Prueba obtener token con contraseña incorrecta."""
        response = api_client.post("/api/auth/token/", {
            "username": "student",
            "password": "wrongpassword"
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token(self, api_client, student_user):
        """Prueba refrescar el token."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(student_user)

        response = api_client.post("/api/auth/refresh/", {
            "refresh": str(refresh)
        })
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data


@pytest.mark.integration
class TestUserManagementEndpoints:
    """Tests para los endpoints de gestión de usuarios."""

    def test_list_users_as_admin(self, admin_client):
        """Prueba listar usuarios como admin."""
        response = admin_client.get("/api/accounts/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_as_student_forbidden(self, authenticated_client):
        """Prueba que estudiantes no pueden listar usuarios."""
        response = authenticated_client.get("/api/accounts/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_user_details(self, admin_client, student_user):
        """Prueba obtener detalles de un usuario."""
        response = admin_client.get(f"/api/accounts/{student_user.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "student"

    def test_create_user_as_admin(self, admin_client):
        """Prueba crear usuario como admin."""
        response = admin_client.post("/api/accounts/create_user/", {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User"
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["username"] == "newuser"

    def test_create_user_as_student_forbidden(self, authenticated_client):
        """Prueba que estudiantes no pueden crear usuarios."""
        response = authenticated_client.post("/api/accounts/create_user/", {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123"
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_assign_role_as_admin(self, admin_client, student_user, instructor_role):
        """Prueba asignar rol como admin."""
        response = admin_client.post(
            f"/api/accounts/{student_user.id}/assign_role/",
            {"role_name": "instructor"}
        )
        assert response.status_code == status.HTTP_200_OK
        student_user.refresh_from_db()
        assert student_user.role.name == "instructor"

    def test_get_statistics_as_admin(self, admin_client):
        """Prueba obtener estadísticas como admin."""
        response = admin_client.get("/api/accounts/statistics/")
        assert response.status_code == status.HTTP_200_OK
        assert "total_users" in response.data

    def test_get_statistics_as_student_forbidden(self, authenticated_client):
        """Prueba que estudiantes no pueden ver estadísticas."""
        response = authenticated_client.get("/api/accounts/statistics/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
