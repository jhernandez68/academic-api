"""
Tests CRÍTICOS - Solo los 5 endpoints que necesitaban fixes.

Este archivo contiene SOLO los tests para los endpoints documentados en TESTING_GUIDE
que tenían problemas. Después de los fixes, todos deberían pasar al 100%.

Endpoints testeados:
1. POST /api/accounts/{id}/assign_role/ - Asignar rol a usuario
2. POST /api/accounts/{id}/change_role/ - Cambiar rol de usuario
3. POST /api/subjects/instructor/close/ - Cerrar materia
4. GET /api/accounts/statistics/ - Ver estadísticas del sistema
5. GET /api/reports/instructor/{id}/ - Descargar reporte de instructor
"""

import pytest
from decimal import Decimal
from rest_framework import status
from django.contrib.auth import get_user_model

from accounts.models import Role
from subjects.models import Subject, Enrollment

User = get_user_model()


@pytest.mark.critical
class TestAssignRoleEndpoint:
    """
    TEST #1: POST /api/accounts/{id}/assign_role/

    Verifica que un admin puede asignar roles a usuarios existentes.
    El parámetro es "role" (no "role_name").
    """

    def test_assign_role_student(self, admin_client, student_user):
        """Prueba asignar rol student a un usuario sin rol."""
        user = User.objects.create_user(
            username="noroluser",
            email="norole@test.com",
            password="pass123"
        )

        response = admin_client.post(
            f"/api/accounts/{user.id}/assign_role/",
            {"role": "student"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"]["name"] == "student"

        # Verificar que se creó el perfil
        user.refresh_from_db()
        assert hasattr(user, "student")

    def test_assign_role_instructor(self, admin_client):
        """Prueba asignar rol instructor a un usuario."""
        user = User.objects.create_user(
            username="instuser",
            email="inst@test.com",
            password="pass123"
        )

        response = admin_client.post(
            f"/api/accounts/{user.id}/assign_role/",
            {"role": "instructor"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"]["name"] == "instructor"

    def test_assign_role_forbidden_for_student(self, authenticated_client, student_user):
        """Prueba que estudiantes NO pueden asignar roles."""
        other_user = User.objects.create_user(
            username="other",
            email="other@test.com",
            password="pass123"
        )

        response = authenticated_client.post(
            f"/api/accounts/{other_user.id}/assign_role/",
            {"role": "student"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_assign_role_correct_parameter_name(self, admin_client):
        """Prueba que el parámetro correcto es 'role' (no 'role_name')."""
        user = User.objects.create_user(
            username="paramtest",
            email="param@test.com",
            password="pass123"
        )

        # Con parámetro correcto
        response = admin_client.post(
            f"/api/accounts/{user.id}/assign_role/",
            {"role": "student"}
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.critical
class TestChangeRoleEndpoint:
    """
    TEST #2: POST /api/accounts/{id}/change_role/

    Verifica que un admin puede cambiar el rol de un usuario que ya tiene uno.
    Este endpoint fue faltante y ahora está implementado.
    """

    def test_change_role_from_student_to_instructor(self, admin_client, student_user):
        """Prueba cambiar rol de student a instructor."""
        response = admin_client.post(
            f"/api/accounts/{student_user.id}/change_role/",
            {"role": "instructor"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"]["name"] == "instructor"

        student_user.refresh_from_db()
        assert student_user.role.name == "instructor"

    def test_change_role_from_instructor_to_admin(self, admin_client, instructor_user):
        """Prueba cambiar rol de instructor a admin."""
        response = admin_client.post(
            f"/api/accounts/{instructor_user.id}/change_role/",
            {"role": "admin"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["role"]["name"] == "admin"

    def test_change_role_forbidden_for_student(self, authenticated_client, student_user, instructor_user):
        """Prueba que estudiantes NO pueden cambiar roles."""
        response = authenticated_client.post(
            f"/api/accounts/{instructor_user.id}/change_role/",
            {"role": "admin"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_change_role_creates_profile_if_needed(self, admin_client, student_user):
        """Prueba que cambiar a instructor crea el perfil automáticamente."""
        # Primero borrar el perfil de instructor si existe
        if hasattr(student_user, "instructor"):
            student_user.instructor.delete()

        response = admin_client.post(
            f"/api/accounts/{student_user.id}/change_role/",
            {"role": "instructor"}
        )

        assert response.status_code == status.HTTP_200_OK

        student_user.refresh_from_db()
        assert hasattr(student_user, "instructor")


@pytest.mark.critical
class TestCloseSubjectEndpoint:
    """
    TEST #3: POST /api/subjects/instructor/close/

    Verifica que un instructor puede cerrar una materia cuando todos
    los estudiantes han sido calificados.
    """

    def test_close_subject_all_graded(self, instructor_client, instructor_user, db):
        """Prueba cerrar materia cuando todos están calificados."""
        # Crear materia nueva asignada al instructor
        subject = Subject.objects.create(
            name="Close Test Subject 1",
            code="CLOSE001",
            credits=3,
            assigned_instructor=instructor_user
        )

        # Crear 2 estudiantes inscritos con calificaciones
        for i in range(2):
            student = User.objects.create_user(
                username=f"closestud{i}",
                email=f"close{i}@test.com",
                password="pass123",
                role=Role.objects.get(name="student")
            )
            Enrollment.objects.create(
                student=student,
                subject=subject,
                state="enrolled",
                grade=Decimal("4.0")
            )

        # Cerrar materia
        response = instructor_client.post(
            "/api/subjects/instructor/close/",
            {"subject_id": subject.id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["closed"] is True

        # Verificar que todas las inscripciones están "closed"
        enrollments = Enrollment.objects.filter(subject=subject)
        for enrollment in enrollments:
            assert enrollment.state == "closed"

    def test_cannot_close_subject_with_uncalified(self, instructor_client, instructor_user, db):
        """Prueba que NO se puede cerrar si hay estudiantes sin calificar."""
        # Crear materia nueva asignada al instructor
        subject = Subject.objects.create(
            name="Close Test Subject 2",
            code="CLOSE002",
            credits=3,
            assigned_instructor=instructor_user
        )

        # Crear estudiante SIN calificación
        student = User.objects.create_user(
            username="uncalif",
            email="uncalif@test.com",
            password="pass123",
            role=Role.objects.get(name="student")
        )
        Enrollment.objects.create(
            student=student,
            subject=subject,
            state="enrolled",
            grade=None  # Sin calificación
        )

        response = instructor_client.post(
            "/api/subjects/instructor/close/",
            {"subject_id": subject.id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["closed"] is False

    def test_close_subject_only_assigned_instructor(self, instructor_client, instructor_user):
        """Prueba que solo el instructor asignado puede cerrar."""
        # Crear materia asignada a OTRO instructor
        other_instructor = User.objects.create_user(
            username="otherinst",
            email="other@test.com",
            password="pass123",
            role=Role.objects.get(name="instructor")
        )
        subject = Subject.objects.create(
            name="Other Subject",
            code="OTH999",
            credits=3,
            assigned_instructor=other_instructor
        )

        response = instructor_client.post(
            "/api/subjects/instructor/close/",
            {"subject_id": subject.id}
        )

        # Debería fallar porque el instructor no es el asignado
        assert response.status_code == status.HTTP_200_OK
        assert response.data["closed"] is False


@pytest.mark.critical
class TestStatisticsEndpoint:
    """
    TEST #4: GET /api/accounts/statistics/

    Verifica que el endpoint retorna todas las estadísticas esperadas
    del sistema académico.
    """

    def test_statistics_has_all_required_fields(self, admin_client):
        """Prueba que la respuesta contiene todos los campos requeridos."""
        response = admin_client.get("/api/accounts/statistics/")

        assert response.status_code == status.HTTP_200_OK

        # Verificar que todos los campos existen
        assert "users" in response.data
        assert "subjects" in response.data
        assert "enrollments" in response.data
        assert "academic_performance" in response.data
        assert "grade_distribution" in response.data
        assert "professors_with_assignments" in response.data

    def test_statistics_users_structure(self, admin_client):
        """Prueba que la estructura de usuarios es correcta."""
        response = admin_client.get("/api/accounts/statistics/")

        users = response.data["users"]
        assert "total_students" in users
        assert "total_instructors" in users
        assert "total_admins" in users
        assert "active_students" in users
        assert "inactive_students" in users

    def test_statistics_subjects_structure(self, admin_client):
        """Prueba que la estructura de materias es correcta."""
        response = admin_client.get("/api/accounts/statistics/")

        subjects = response.data["subjects"]
        assert "total_subjects" in subjects
        assert "subjects_with_instructor" in subjects
        assert "subjects_without_instructor" in subjects
        assert "avg_subjects_per_instructor" in subjects

    def test_statistics_enrollments_structure(self, admin_client):
        """Prueba que la estructura de inscripciones es correcta."""
        response = admin_client.get("/api/accounts/statistics/")

        enrollments = response.data["enrollments"]
        assert "total_enrollments" in enrollments
        assert "enrollments_enrolled" in enrollments
        assert "enrollments_approved" in enrollments
        assert "enrollments_failed" in enrollments
        assert "enrollments_closed" in enrollments

    def test_statistics_academic_performance_structure(self, admin_client):
        """Prueba que la estructura de desempeño académico es correcta."""
        response = admin_client.get("/api/accounts/statistics/")

        perf = response.data["academic_performance"]
        assert "approval_rate" in perf
        assert "failure_rate" in perf
        assert "system_average_grade" in perf
        assert "average_student_gpa" in perf

    def test_statistics_grade_distribution_structure(self, admin_client):
        """Prueba que la distribución de calificaciones es correcta."""
        response = admin_client.get("/api/accounts/statistics/")

        dist = response.data["grade_distribution"]
        assert "0_1" in dist
        assert "1_2" in dist
        assert "2_3" in dist
        assert "3_4" in dist
        assert "4_5" in dist

    def test_statistics_forbidden_for_student(self, authenticated_client):
        """Prueba que estudiantes NO pueden ver estadísticas."""
        response = authenticated_client.get("/api/accounts/statistics/")

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.critical
class TestInstructorReportEndpoint:
    """
    TEST #5: GET /api/reports/instructor/{id}/

    Verifica que los reportes de instructor funcionan correctamente
    con validación de permisos.
    """

    def test_instructor_can_download_own_report(self, instructor_client, instructor_user):
        """Prueba que un instructor puede descargar su propio reporte."""
        response = instructor_client.get(f"/api/reports/instructor/{instructor_user.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

    def test_admin_can_download_any_instructor_report(self, admin_client, instructor_user):
        """Prueba que admin puede descargar reportes de cualquier instructor."""
        response = admin_client.get(f"/api/reports/instructor/{instructor_user.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"

    def test_student_cannot_download_instructor_report(self, authenticated_client, instructor_user):
        """Prueba que estudiantes NO pueden descargar reportes de instructores."""
        response = authenticated_client.get(f"/api/reports/instructor/{instructor_user.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_cannot_download_other_instructor_report(self, instructor_client, instructor_user):
        """Prueba que un instructor NO puede descargar reportes de otro instructor."""
        other_instructor = User.objects.create_user(
            username="otherinst2",
            email="other2@test.com",
            password="pass123",
            role=Role.objects.get(name="instructor")
        )

        response = instructor_client.get(f"/api/reports/instructor/{other_instructor.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_report_includes_assigned_subjects(self, instructor_client, instructor_user):
        """Prueba que el reporte incluye las materias asignadas."""
        # Crear materia asignada
        subject = Subject.objects.create(
            name="Test Subject",
            code="TST123",
            credits=3,
            assigned_instructor=instructor_user
        )

        # Crear inscripciones con calificaciones
        student = User.objects.create_user(
            username="reportstud",
            email="reportstud@test.com",
            password="pass123",
            role=Role.objects.get(name="student")
        )
        Enrollment.objects.create(
            student=student,
            subject=subject,
            state="approved",
            grade=Decimal("4.5")
        )

        response = instructor_client.get(f"/api/reports/instructor/{instructor_user.id}/")

        assert response.status_code == status.HTTP_200_OK
        content = response.content.decode()
        assert subject.name in content

    def test_report_format_is_csv(self, instructor_client, instructor_user):
        """Prueba que el reporte está en formato CSV."""
        response = instructor_client.get(f"/api/reports/instructor/{instructor_user.id}/")

        assert response.status_code == status.HTTP_200_OK
        content = response.content.decode()

        # CSV debe tener encabezados
        assert "Name" in content
        assert "Subject" in content
        assert "Average" in content

    def test_report_includes_averages(self, instructor_client, instructor_user):
        """Prueba que el reporte calcula correctamente los promedios."""
        subject = Subject.objects.create(
            name="Avg Test",
            code="AVG999",
            credits=3,
            assigned_instructor=instructor_user
        )

        # Crear 3 estudiantes con calificaciones diferentes
        grades = [Decimal("3.0"), Decimal("4.0"), Decimal("5.0")]
        for i, grade in enumerate(grades):
            student = User.objects.create_user(
                username=f"avgstud{i}",
                email=f"avg{i}@test.com",
                password="pass123",
                role=Role.objects.get(name="student")
            )
            Enrollment.objects.create(
                student=student,
                subject=subject,
                state="approved",
                grade=grade
            )

        response = instructor_client.get(f"/api/reports/instructor/{instructor_user.id}/")

        assert response.status_code == status.HTTP_200_OK
        content = response.content.decode()

        # El promedio debería ser 4.0 (3+4+5)/3
        assert "4.0" in content
