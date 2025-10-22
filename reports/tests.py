"""
Tests para la aplicación de reportes.

Cobertura:
- Vistas: Generar reportes CSV
- Servicios: Recopilación de datos para reportes
- Permisos: Acceso a reportes
- Formatos: CSV, validación de contenido
"""

import pytest
import csv
from io import StringIO
from decimal import Decimal
from rest_framework import status

from subjects.models import Enrollment


@pytest.mark.integration
class TestReportEndpoints:
    """Tests para endpoints de reportes."""

    def test_student_report_endpoint(self, authenticated_client, student_user):
        """Prueba obtener reporte de estudiante."""
        response = authenticated_client.get(f"/api/reports/student/{student_user.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.get("Content-Type", "").startswith("text/csv")

    def test_instructor_report_endpoint(self, instructor_client, instructor_user):
        """Prueba obtener reporte de instructor."""
        response = instructor_client.get(f"/api/reports/instructor/{instructor_user.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.get("Content-Type", "").startswith("text/csv")

    def test_cannot_access_other_student_report(self, authenticated_client, student_user, db, student_role):
        """Prueba que un estudiante no puede ver reporte de otro."""
        User = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model()
        other_student = User.objects.create_user(
            username="other_student",
            email="other@example.com",
            password="pass123",
            role=student_role
        )

        response = authenticated_client.get(f"/api/reports/student/{other_student.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_any_report(self, admin_client, student_user):
        """Prueba que admin puede ver reportes de cualquier usuario."""
        response = admin_client.get(f"/api/reports/student/{student_user.id}/")
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_access_report(self, api_client, student_user):
        """Prueba que usuarios sin autenticar no pueden acceder a reportes."""
        response = api_client.get(f"/api/reports/student/{student_user.id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
class TestStudentReportContent:
    """Tests para el contenido del reporte de estudiante."""

    def test_report_includes_basic_info(self, authenticated_client, student_user):
        """Prueba que el reporte incluye información básica."""
        response = authenticated_client.get(f"/api/reports/student/{student_user.id}/")
        assert response.status_code == status.HTTP_200_OK

        # Verificar que contiene el nombre
        content = response.content.decode()
        assert student_user.first_name in content or student_user.last_name in content

    def test_report_includes_enrollments(self, authenticated_client, enrollment):
        """Prueba que el reporte incluye las inscripciones."""
        response = authenticated_client.get(
            f"/api/reports/student/{enrollment.student.id}/"
        )
        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode()
        assert enrollment.subject.name in content or enrollment.subject.code in content

    def test_report_includes_grades(self, authenticated_client, graded_enrollment):
        """Prueba que el reporte incluye calificaciones."""
        response = authenticated_client.get(
            f"/api/reports/student/{graded_enrollment.student.id}/"
        )
        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode()
        assert str(graded_enrollment.grade) in content or "4.5" in content

    def test_report_includes_status(self, authenticated_client, graded_enrollment):
        """Prueba que el reporte incluye estado (aprobada/reprobada)."""
        response = authenticated_client.get(
            f"/api/reports/student/{graded_enrollment.student.id}/"
        )
        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode()
        # Debe incluir "approved" o similar
        assert "approved" in content.lower() or "aprobada" in content.lower()

    def test_report_includes_gpa(self, authenticated_client, graded_enrollment):
        """Prueba que el reporte incluye el GPA."""
        response = authenticated_client.get(
            f"/api/reports/student/{graded_enrollment.student.id}/"
        )
        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode()
        # Debe incluir "GPA" o "promedio"
        assert "gpa" in content.lower() or "promedio" in content.lower()


@pytest.mark.unit
class TestInstructorReportContent:
    """Tests para el contenido del reporte de instructor."""

    def test_report_includes_assigned_subjects(self, instructor_client, subject_without_prerequisites):
        """Prueba que el reporte incluye materias asignadas."""
        response = instructor_client.get(
            f"/api/reports/instructor/{subject_without_prerequisites.assigned_instructor.id}/"
        )
        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode()
        assert subject_without_prerequisites.name in content

    def test_report_includes_student_grades(self, instructor_client, graded_enrollment):
        """Prueba que el reporte incluye calificaciones de estudiantes."""
        response = instructor_client.get(
            f"/api/reports/instructor/{graded_enrollment.subject.assigned_instructor.id}/"
        )
        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode()
        # Debe incluir información de calificación
        assert "grade" in content.lower() or str(graded_enrollment.grade) in content

    def test_report_includes_subject_average(self, instructor_client, multiple_subjects):
        """Prueba que el reporte incluye promedio de materia."""
        instructor = multiple_subjects[0].assigned_instructor
        response = instructor_client.get(f"/api/reports/instructor/{instructor.id}/")
        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode()
        # Debe incluir información de promedio
        assert "average" in content.lower() or "promedio" in content.lower()


@pytest.mark.integration
class TestReportFormatting:
    """Tests para validar formato CSV de reportes."""

    def test_student_report_is_valid_csv(self, authenticated_client, enrollment):
        """Prueba que el reporte es un CSV válido."""
        response = authenticated_client.get(
            f"/api/reports/student/{enrollment.student.id}/"
        )
        assert response.status_code == status.HTTP_200_OK

        # Intentar parsear como CSV
        try:
            content = response.content.decode()
            reader = csv.reader(StringIO(content))
            rows = list(reader)
            assert len(rows) > 0  # Al menos encabezados
        except Exception as e:
            pytest.fail(f"CSV parsing failed: {e}")

    def test_instructor_report_is_valid_csv(self, instructor_client, subject_without_prerequisites):
        """Prueba que el reporte de instructor es un CSV válido."""
        response = instructor_client.get(
            f"/api/reports/instructor/{subject_without_prerequisites.assigned_instructor.id}/"
        )
        assert response.status_code == status.HTTP_200_OK

        try:
            content = response.content.decode()
            reader = csv.reader(StringIO(content))
            rows = list(reader)
            assert len(rows) > 0
        except Exception as e:
            pytest.fail(f"CSV parsing failed: {e}")

    def test_report_has_headers(self, authenticated_client, enrollment):
        """Prueba que el reporte tiene encabezados."""
        response = authenticated_client.get(
            f"/api/reports/student/{enrollment.student.id}/"
        )

        content = response.content.decode()
        lines = content.strip().split("\n")
        headers = lines[0].split(",")

        # Debe tener al menos algunos encabezados
        assert len(headers) > 0
        # Los encabezados no deben estar vacíos
        assert all(h.strip() for h in headers)


@pytest.mark.integration
class TestReportPermissions:
    """Tests para permisos en reportes."""

    def test_student_can_only_access_own_report(self, authenticated_client, student_user, db, student_role):
        """Prueba que estudiante solo puede acceder a su propio reporte."""
        User = __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model()
        other_student = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="pass123",
            role=student_role
        )

        # Su propio reporte - OK
        response = authenticated_client.get(f"/api/reports/student/{student_user.id}/")
        assert response.status_code == status.HTTP_200_OK

        # Reporte de otro - Forbidden
        response = authenticated_client.get(f"/api/reports/student/{other_student.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_access_own_report(self, instructor_client, instructor_user):
        """Prueba que instructor puede acceder a su propio reporte."""
        response = instructor_client.get(f"/api/reports/instructor/{instructor_user.id}/")
        assert response.status_code == status.HTTP_200_OK

    def test_admin_can_access_all_reports(self, admin_client, student_user, instructor_user):
        """Prueba que admin puede acceder a todos los reportes."""
        # Reporte de estudiante
        response = admin_client.get(f"/api/reports/student/{student_user.id}/")
        assert response.status_code == status.HTTP_200_OK

        # Reporte de instructor
        response = admin_client.get(f"/api/reports/instructor/{instructor_user.id}/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestReportWithComplexData:
    """Tests de reporte con datos complejos."""

    def test_report_with_multiple_enrollments(self, authenticated_client, student_user, multiple_subjects):
        """Prueba reporte con múltiples inscripciones."""
        # Crear varias inscripciones
        for subject in multiple_subjects:
            Enrollment.objects.create(
                student=student_user,
                subject=subject,
                state="approved",
                grade=Decimal("4.0")
            )

        response = authenticated_client.get(f"/api/reports/student/{student_user.id}/")
        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode()
        # Debe contener información de todas las materias
        for subject in multiple_subjects:
            assert subject.code in content

    def test_report_with_mixed_grades(self, authenticated_client, student_user, multiple_subjects):
        """Prueba reporte con calificaciones mixtas (aprobadas y reprobadas)."""
        # Algunas aprobadas
        for subject in multiple_subjects[:2]:
            Enrollment.objects.create(
                student=student_user,
                subject=subject,
                state="approved",
                grade=Decimal("4.0")
            )

        # Algunas reprobadas
        for subject in multiple_subjects[2:]:
            Enrollment.objects.create(
                student=student_user,
                subject=subject,
                state="failed",
                grade=Decimal("2.0")
            )

        response = authenticated_client.get(f"/api/reports/student/{student_user.id}/")
        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode()
        # Debe mostrar ambos estados
        assert "approved" in content.lower() or "aprobada" in content.lower()
        assert "failed" in content.lower() or "reprobada" in content.lower()

    def test_report_empty_for_new_student(self, authenticated_client, student_user):
        """Prueba que reporte está vacío para estudiante sin inscripciones."""
        response = authenticated_client.get(f"/api/reports/student/{student_user.id}/")
        assert response.status_code == status.HTTP_200_OK

        # Debe al menos contener encabezados
        content = response.content.decode()
        assert len(content) > 0
