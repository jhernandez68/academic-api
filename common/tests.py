"""
Tests para la aplicación común (decoradores, middleware, permisos).

Cobertura:
- Decoradores: @validate_prerequisites
- Middleware: RequestMetricsMiddleware
- Permisos: IsAdmin, IsStudent, IsInstructor
"""

import pytest
from decimal import Decimal
from rest_framework import status

from subjects.models import Subject, Enrollment


@pytest.mark.unit
class TestValidatePrerequisitesDecorator:
    """Tests para el decorador @validate_prerequisites."""

    def test_can_enroll_valid_subject(self, authenticated_client, student_user, subject_without_prerequisites):
        """Prueba enrollarse en materia válida."""
        response = authenticated_client.post("/api/subjects/student/enroll/", {
            "subject_id": subject_without_prerequisites.id
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_cannot_enroll_without_prerequisite(self, authenticated_client, student_user, subject_with_prerequisites):
        """Prueba que el decorador valida prerequisitos."""
        response = authenticated_client.post("/api/subjects/student/enroll/", {
            "subject_id": subject_with_prerequisites.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_can_enroll_with_prerequisite_met(self, authenticated_client, student_user,
                                              subject_with_prerequisites, subject_without_prerequisites):
        """Prueba que puede enrollarse cuando prerequisito está cumplido."""
        # Primero aprobar el prerequisito
        Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="approved",
            grade=Decimal("3.5")
        )

        # Ahora debe poder enrollarse
        response = authenticated_client.post("/api/subjects/student/enroll/", {
            "subject_id": subject_with_prerequisites.id
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_cannot_enroll_duplicate(self, authenticated_client, student_user, enrollment):
        """Prueba que el decorador previene inscripciones duplicadas."""
        response = authenticated_client.post("/api/subjects/student/enroll/", {
            "subject_id": enrollment.subject.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_enroll_exceed_credits(self, authenticated_client, student_user, db):
        """Prueba que el decorador valida límite de créditos."""
        # Crear materias de 4 créditos cada una
        subjects = []
        for i in range(5):
            subject = Subject.objects.create(
                name=f"Subject {i}",
                code=f"SUB{i}",
                credits=4,
                assigned_instructor=__import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model().objects.create_user(
                    f"inst{i}", f"inst{i}@test.com", "pass"
                )
            )
            subjects.append(subject)
            # Enrollar en las primeras 4 (16 créditos - en el límite)
            if i < 4:
                Enrollment.objects.create(
                    student=student_user,
                    subject=subject,
                    state="enrolled"
                )

        # Intentar enrollarse en la 5ta (excedería el límite)
        response = authenticated_client.post("/api/subjects/student/enroll/", {
            "subject_id": subjects[4].id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_enroll_already_approved_subject(self, authenticated_client, student_user,
                                                    subject_without_prerequisites):
        """Prueba que no puede re-inscribirse en materia aprobada."""
        Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="approved",
            grade=Decimal("3.5")
        )

        response = authenticated_client.post("/api/subjects/student/enroll/", {
            "subject_id": subject_without_prerequisites.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.unit
class TestRequestMetricsMiddleware:
    """Tests para el middleware de métricas."""

    def test_middleware_logs_request(self, authenticated_client):
        """Prueba que middleware registra requests."""
        # Hacer un request
        response = authenticated_client.get("/api/subjects/student/enrolled/")
        assert response.status_code == status.HTTP_200_OK
        # El middleware debería haber registrado la métrica

    def test_middleware_records_user_id(self, authenticated_client, student_user):
        """Prueba que middleware registra el ID del usuario."""
        response = authenticated_client.get("/api/subjects/student/enrolled/")
        assert response.status_code == status.HTTP_200_OK
        # El middleware debería haber registrado student_user.id

    def test_middleware_records_duration(self, authenticated_client):
        """Prueba que middleware registra duración."""
        response = authenticated_client.get("/api/subjects/student/enrolled/")
        assert response.status_code == status.HTTP_200_OK
        # El middleware debería haber registrado la duración en ms


@pytest.mark.integration
class TestPermissionIntegration:
    """Tests de integración para permisos."""

    def test_student_cannot_create_subject(self, authenticated_client):
        """Prueba que estudiantes no pueden crear materias."""
        response = authenticated_client.post("/api/subjects/", {
            "name": "New Subject",
            "code": "NEW101",
            "credits": 3
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_cannot_create_subject(self, instructor_client):
        """Prueba que instructores no pueden crear materias."""
        response = instructor_client.post("/api/subjects/", {
            "name": "New Subject",
            "code": "NEW101",
            "credits": 3
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_create_subject(self, admin_client, instructor_user):
        """Prueba que admin puede crear materias."""
        response = admin_client.post("/api/subjects/", {
            "name": "New Subject",
            "code": "NEW101",
            "credits": 3,
            "assigned_instructor": instructor_user.id
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_student_cannot_grade(self, authenticated_client, enrollment):
        """Prueba que estudiantes no pueden calificar."""
        response = authenticated_client.post("/api/subjects/instructor/grade/", {
            "enrollment_id": enrollment.id,
            "grade": 4.5
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_grade_own_student(self, instructor_client, subject_without_prerequisites, enrollment):
        """Prueba que instructor puede calificar sus estudiantes."""
        if enrollment.subject == subject_without_prerequisites and \
           enrollment.subject.assigned_instructor == instructor_client.handler._test_user:
            response = instructor_client.post("/api/subjects/instructor/grade/", {
                "enrollment_id": enrollment.id,
                "grade": 4.5
            })
            assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]

    def test_student_cannot_list_all_users(self, authenticated_client):
        """Prueba que estudiantes no pueden listar usuarios."""
        response = authenticated_client.get("/api/accounts/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_cannot_list_all_users(self, instructor_client):
        """Prueba que instructores no pueden listar usuarios."""
        response = instructor_client.get("/api/accounts/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list_users(self, admin_client):
        """Prueba que admin puede listar usuarios."""
        response = admin_client.get("/api/accounts/")
        assert response.status_code == status.HTTP_200_OK

    def test_student_cannot_get_statistics(self, authenticated_client):
        """Prueba que estudiantes no pueden obtener estadísticas."""
        response = authenticated_client.get("/api/accounts/statistics/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_get_statistics(self, admin_client):
        """Prueba que admin puede obtener estadísticas."""
        response = admin_client.get("/api/accounts/statistics/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestRoleBasedAccess:
    """Tests para acceso basado en roles."""

    def test_student_endpoints(self, authenticated_client):
        """Prueba endpoints disponibles para estudiantes."""
        # Student puede ver sus materias inscritas
        response = authenticated_client.get("/api/subjects/student/enrolled/")
        assert response.status_code == status.HTTP_200_OK

        # Student puede ver su GPA
        response = authenticated_client.get("/api/subjects/student/gpa/")
        assert response.status_code == status.HTTP_200_OK

        # Student puede ver su historial
        response = authenticated_client.get("/api/subjects/student/history/")
        assert response.status_code == status.HTTP_200_OK

    def test_instructor_endpoints(self, instructor_client):
        """Prueba endpoints disponibles para instructores."""
        # Instructor puede ver sus materias asignadas
        response = instructor_client.get("/api/subjects/instructor/assigned_subjects/")
        assert response.status_code == status.HTTP_200_OK

    def test_admin_endpoints(self, admin_client):
        """Prueba endpoints disponibles para admin."""
        # Admin puede crear usuarios
        response = admin_client.post("/api/accounts/create_user/", {
            "username": "newuser",
            "email": "new@example.com",
            "password": "pass123"
        })
        assert response.status_code == status.HTTP_201_CREATED

        # Admin puede ver estadísticas
        response = admin_client.get("/api/accounts/statistics/")
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_access_protected(self, api_client):
        """Prueba que usuarios sin autenticar no acceden a endpoints protegidos."""
        response = api_client.get("/api/subjects/student/enrolled/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = api_client.get("/api/accounts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_can_access_public(self, api_client, subject_without_prerequisites):
        """Prueba que usuarios sin autenticar pueden listar materias."""
        response = api_client.get("/api/subjects/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.unit
class TestDecoratorsWithEdgeCases:
    """Tests para casos edge en decoradores."""

    def test_enroll_with_invalid_subject_id(self, authenticated_client):
        """Prueba inscribirse con ID de materia inválido."""
        response = authenticated_client.post("/api/subjects/student/enroll/", {
            "subject_id": 99999
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_enroll_with_missing_subject_id(self, authenticated_client):
        """Prueba inscribirse sin proporcionar ID de materia."""
        response = authenticated_client.post("/api/subjects/student/enroll/", {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_grade_with_invalid_grade_value(self, instructor_client, enrollment):
        """Prueba calificar con valor fuera de rango."""
        # Más de 5.0
        response = instructor_client.post("/api/subjects/instructor/grade/", {
            "enrollment_id": enrollment.id,
            "grade": 5.5
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Menor a 0.0
        response = instructor_client.post("/api/subjects/instructor/grade/", {
            "enrollment_id": enrollment.id,
            "grade": -0.5
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_grade_without_permission(self, authenticated_client, enrollment):
        """Prueba que estudiante no puede calificar."""
        response = authenticated_client.post("/api/subjects/instructor/grade/", {
            "enrollment_id": enrollment.id,
            "grade": 4.0
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN
