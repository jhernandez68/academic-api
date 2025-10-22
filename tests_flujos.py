"""
Tests SOLO para los Flujos del TESTING_GUIDE

Este archivo contiene tests ÚNICAMENTE para:
1. Flujo Estudiante (endpoints 11-17 del TESTING_GUIDE)
2. Flujo Profesor (endpoints 18-22 del TESTING_GUIDE)

Los flujos representan las interacciones principales de los usuarios
en el sistema académico.
"""

import pytest
from decimal import Decimal
from rest_framework import status
from django.contrib.auth import get_user_model

from accounts.models import Role
from subjects.models import Subject, Enrollment

User = get_user_model()


# ============================================================================
# FLUJO ESTUDIANTE
# ============================================================================

@pytest.mark.flujo_estudiante
class TestFlujoEstudiante:
    """
    Pruebas para el FLUJO ESTUDIANTE.

    El estudiante puede:
    - Inscribirse en materias
    - Ver materias inscritas
    - Ver materias aprobadas
    - Ver materias reprobadas
    - Ver su promedio general (GPA)
    - Ver su histórico académico completo
    """

    def test_11_login_estudiante(self, api_client, student_user):
        """
        TEST #11: Login como Estudiante
        POST /api/auth/token/

        El estudiante obtiene su token JWT para autenticarse.
        """
        response = api_client.post("/api/auth/token/", {
            "username": "student",
            "password": "student123"
        })

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_12_inscribirse_en_materia(self, authenticated_client, student_user, subject_without_prerequisites):
        """
        TEST #12: Inscribirse en Materia
        POST /api/subjects/student/enroll/

        El estudiante se inscribe en una materia disponible.
        """
        response = authenticated_client.post(
            "/api/subjects/student/enroll/",
            {"subject_id": subject_without_prerequisites.id}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.data

    def test_13_ver_materias_inscritas(self, authenticated_client, enrollment):
        """
        TEST #13: Ver Materias Inscritas
        GET /api/subjects/student/enrolled/

        El estudiante ve todas las materias en las que está actualmente inscrito.
        """
        response = authenticated_client.get("/api/subjects/student/enrolled/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0

        # Verificar estructura de respuesta
        enrollment_data = response.data[0]
        assert "id" in enrollment_data
        assert "student" in enrollment_data
        assert "subject" in enrollment_data
        assert "state" in enrollment_data
        assert "grade" in enrollment_data
        assert "created_at" in enrollment_data

        # Verificar que el estado es "enrolled"
        assert enrollment_data["state"] == "enrolled"

    def test_14_ver_materias_aprobadas(self, authenticated_client, graded_enrollment):
        """
        TEST #14: Ver Materias Aprobadas
        GET /api/subjects/student/approved/

        El estudiante ve todas las materias que ha aprobado (calificación >= 3.0).
        """
        response = authenticated_client.get("/api/subjects/student/approved/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0

        # Verificar que todas las materias tienen estado "approved"
        for enrollment_data in response.data:
            assert enrollment_data["state"] == "approved"
            assert enrollment_data["grade"] is not None
            assert float(enrollment_data["grade"]) >= 3.0

    def test_15_ver_materias_reprobadas(self, authenticated_client, failed_enrollment):
        """
        TEST #15: Ver Materias Reprobadas
        GET /api/subjects/student/failed/

        El estudiante ve todas las materias que ha reprobado (calificación < 3.0).
        """
        response = authenticated_client.get("/api/subjects/student/failed/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0

        # Verificar que todas tienen estado "failed"
        for enrollment_data in response.data:
            assert enrollment_data["state"] == "failed"
            assert enrollment_data["grade"] is not None
            assert float(enrollment_data["grade"]) < 3.0

    def test_16_ver_promedio_gpa(self, authenticated_client, graded_enrollment):
        """
        TEST #16: Ver Promedio General (GPA)
        GET /api/subjects/student/gpa/

        El estudiante obtiene su promedio general acumulado.
        """
        response = authenticated_client.get("/api/subjects/student/gpa/")

        assert response.status_code == status.HTTP_200_OK
        assert "gpa" in response.data

        # El GPA debe ser un número entre 0.0 y 5.0
        gpa_value = float(response.data["gpa"])
        assert 0.0 <= gpa_value <= 5.0

    def test_17_ver_historico_academico(self, authenticated_client, enrollment):
        """
        TEST #17: Ver Histórico Académico
        GET /api/subjects/student/history/

        El estudiante obtiene su historial completo de inscripciones,
        incluyendo inscritas, aprobadas y reprobadas.
        """
        response = authenticated_client.get("/api/subjects/student/history/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0

        # Verificar estructura de cada inscripción en el historial
        for enrollment_data in response.data:
            assert "id" in enrollment_data
            assert "student" in enrollment_data
            assert "subject" in enrollment_data
            assert "state" in enrollment_data
            assert "created_at" in enrollment_data


# ============================================================================
# FLUJO PROFESOR
# ============================================================================

@pytest.mark.flujo_profesor
class TestFlujoProfesor:
    """
    Pruebas para el FLUJO PROFESOR.

    El profesor puede:
    - Ver sus materias asignadas
    - Ver estudiantes por materia
    - Calificar estudiantes
    - Finalizar materias cuando todos están calificados
    - Ver materias anteriores y promedios
    """

    def test_18_login_profesor(self, api_client, instructor_user):
        """
        TEST #18: Login como Profesor
        POST /api/auth/token/

        El profesor obtiene su token JWT para autenticarse.
        """
        response = api_client.post("/api/auth/token/", {
            "username": "instructor",
            "password": "instructor123"
        })

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_19_ver_materias_asignadas(self, instructor_client, instructor_user, subject_without_prerequisites):
        """
        TEST #19: Ver Materias Asignadas
        GET /api/subjects/instructor/assigned_subjects/

        El profesor ve todas las materias que le han sido asignadas para enseñar.
        """
        # Asignar materia al instructor
        subject_without_prerequisites.assigned_instructor = instructor_user
        subject_without_prerequisites.save()

        response = instructor_client.get("/api/subjects/instructor/assigned_subjects/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0

        # Verificar estructura de materia
        subject_data = response.data[0]
        assert "id" in subject_data
        assert "name" in subject_data
        assert "code" in subject_data
        assert "credits" in subject_data

    def test_20_ver_estudiantes_por_materia(self, instructor_client, instructor_user, subject_without_prerequisites, enrollment):
        """
        TEST #20: Ver Estudiantes por Materia
        GET /api/subjects/instructor/students/?subject_id=X

        El profesor ve todos los estudiantes inscritos en una de sus materias.
        """
        # Asignar materia al instructor
        subject_without_prerequisites.assigned_instructor = instructor_user
        subject_without_prerequisites.save()

        response = instructor_client.get(
            f"/api/subjects/instructor/students/?subject_id={subject_without_prerequisites.id}"
        )

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0

        # Verificar estructura de inscripción
        enrollment_data = response.data[0]
        assert "id" in enrollment_data
        assert "student" in enrollment_data
        assert "subject" in enrollment_data
        assert "state" in enrollment_data

    def test_21_calificar_estudiante(self, instructor_client, instructor_user, enrollment):
        """
        TEST #21: Calificar Estudiante
        POST /api/subjects/instructor/grade/

        El profesor asigna una calificación a un estudiante en una materia.
        La calificación debe estar entre 0.0 y 5.0.
        """
        # Asegurar que el instructor es el asignado
        enrollment.subject.assigned_instructor = instructor_user
        enrollment.subject.save()

        response = instructor_client.post(
            "/api/subjects/instructor/grade/",
            {
                "enrollment_id": enrollment.id,
                "value": 4.5
            }
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["grade"] == 4.5
        # La calificación debe cambiar el estado
        assert response.data["state"] in ["approved", "failed"]

    def test_22_finalizar_materia(self, instructor_client, instructor_user, db):
        """
        TEST #22: Finalizar Materia
        POST /api/subjects/instructor/close/

        El profesor cierra una materia después de haber calificado a todos
        los estudiantes inscritos.
        """
        # Crear materia con estudiantes calificados
        subject = Subject.objects.create(
            name="Final Subject",
            code="FINAL999",
            credits=3,
            assigned_instructor=instructor_user
        )

        # Crear estudiante calificado
        student = User.objects.create_user(
            username="finalstud",
            email="final@test.com",
            password="pass123",
            role=Role.objects.get(name="student")
        )
        Enrollment.objects.create(
            student=student,
            subject=subject,
            state="enrolled",
            grade=Decimal("4.0")
        )

        response = instructor_client.post(
            "/api/subjects/instructor/close/",
            {"subject_id": subject.id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["closed"] is True

    def test_materias_anteriores_y_promedios(self, instructor_client, instructor_user, db):
        """
        Bonus: Ver materias anteriores y promedios

        El profesor puede ver el historial de materias que ha impartido
        y los promedios de calificaciones de cada materia.
        """
        # Crear materia con estudiantes
        subject = Subject.objects.create(
            name="History Subject",
            code="HIST999",
            credits=3,
            assigned_instructor=instructor_user
        )

        # Crear estudiantes con calificaciones
        for i, grade in enumerate([Decimal("4.0"), Decimal("3.5"), Decimal("4.5")]):
            student = User.objects.create_user(
                username=f"histstud{i}",
                email=f"hist{i}@test.com",
                password="pass123",
                role=Role.objects.get(name="student")
            )
            Enrollment.objects.create(
                student=student,
                subject=subject,
                state="approved",
                grade=grade
            )

        # Ver materias asignadas
        response = instructor_client.get("/api/subjects/instructor/assigned_subjects/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) > 0

        # Verificar que la materia está en la lista
        subject_in_list = any(s["id"] == subject.id for s in response.data)
        assert subject_in_list is True


# ============================================================================
# FLUJOS INTEGRADOS
# ============================================================================

@pytest.mark.flujo_integrado
class TestFlujoIntegrado:
    """
    Pruebas de flujo integrado: Estudiante se inscribe y Profesor califica.

    Simula un flujo completo del sistema académico.
    """

    def test_flujo_completo_inscripcion_y_calificacion(self, student_user, instructor_user, db):
        """
        Flujo completo:
        1. Estudiante se inscribe en materia
        2. Profesor ve estudiantes
        3. Profesor califica
        4. Estudiante ve su materia aprobada
        """
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        # Crear materia
        subject = Subject.objects.create(
            name="Integrated Flow",
            code="INTEG001",
            credits=3,
            assigned_instructor=instructor_user
        )

        # 1. ESTUDIANTE SE INSCRIBE
        student_client = APIClient()
        refresh = RefreshToken.for_user(student_user)
        student_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        enroll_response = student_client.post(
            "/api/subjects/student/enroll/",
            {"subject_id": subject.id}
        )
        assert enroll_response.status_code == status.HTTP_201_CREATED
        enrollment_id = enroll_response.data["id"]

        # 2. PROFESOR VE ESTUDIANTES
        instructor_client = APIClient()
        refresh = RefreshToken.for_user(instructor_user)
        instructor_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        students_response = instructor_client.get(
            f"/api/subjects/instructor/students/?subject_id={subject.id}"
        )
        assert students_response.status_code == status.HTTP_200_OK
        assert len(students_response.data) > 0

        # 3. PROFESOR CALIFICA
        grade_response = instructor_client.post(
            "/api/subjects/instructor/grade/",
            {
                "enrollment_id": enrollment_id,
                "value": 4.5
            }
        )
        assert grade_response.status_code == status.HTTP_200_OK
        assert grade_response.data["state"] == "approved"

        # 4. ESTUDIANTE VE MATERIA APROBADA
        approved_response = student_client.get("/api/subjects/student/approved/")
        assert approved_response.status_code == status.HTTP_200_OK
        assert len(approved_response.data) > 0

        # Verificar que la materia está en aprobadas
        subject_in_approved = any(
            e["subject"] == subject.id for e in approved_response.data
        )
        assert subject_in_approved is True

    def test_flujo_estudiante_ve_gpa_actualizado(self, instructor_user, db):
        """
        Flujo: Después de ser calificado, el estudiante puede ver su GPA actualizado.
        """
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        # Crear estudiante fresco para este test
        student_user = User.objects.create_user(
            username="gpa_test_student",
            email="gpa_test@example.com",
            password="pass123",
            role=Role.objects.get(name="student")
        )
        # Crear perfil de estudiante
        from accounts.models import Student
        Student.objects.get_or_create(
            user=student_user,
            defaults={"max_credits_per_term": 16}
        )

        # Crear 3 materias
        subjects = []
        for i in range(3):
            subject = Subject.objects.create(
                name=f"GPA Test {i}",
                code=f"GPA{i:03d}",
                credits=3,
                assigned_instructor=instructor_user
            )
            subjects.append(subject)

        # Cliente de estudiante
        student_client = APIClient()
        refresh = RefreshToken.for_user(student_user)
        student_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Inscribirse en 3 materias
        enrollment_ids = []
        for subject in subjects:
            response = student_client.post(
                "/api/subjects/student/enroll/",
                {"subject_id": subject.id}
            )
            enrollment_ids.append(response.data["id"])

        # Cliente de profesor
        instructor_client = APIClient()
        refresh = RefreshToken.for_user(instructor_user)
        instructor_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        # Calificar con diferentes notas
        grades = [Decimal("5.0"), Decimal("4.0"), Decimal("3.0")]
        for enrollment_id, grade in zip(enrollment_ids, grades):
            instructor_client.post(
                "/api/subjects/instructor/grade/",
                {"enrollment_id": enrollment_id, "value": float(grade)}
            )

        # Ver GPA
        gpa_response = student_client.get("/api/subjects/student/gpa/")
        assert gpa_response.status_code == status.HTTP_200_OK

        # El GPA debe ser el promedio: (5.0 + 4.0 + 3.0) / 3 = 4.0
        expected_gpa = (5.0 + 4.0 + 3.0) / 3
        actual_gpa = float(gpa_response.data["gpa"])
        assert abs(actual_gpa - expected_gpa) < 0.01

    def test_profesor_no_puede_cerrar_con_estudiantes_sin_calificar(self, instructor_client, instructor_user, db):
        """
        Flujo: Profesor intenta cerrar materia pero hay estudiantes sin calificar.
        """
        # Crear materia
        subject = Subject.objects.create(
            name="Uncalified Test",
            code="UNCAL001",
            credits=3,
            assigned_instructor=instructor_user
        )

        # Crear estudiante sin calificar
        student = User.objects.create_user(
            username="uncaliftest",
            email="uncaliftest@test.com",
            password="pass123",
            role=Role.objects.get(name="student")
        )
        Enrollment.objects.create(
            student=student,
            subject=subject,
            state="enrolled",
            grade=None  # SIN CALIFICACIÓN
        )

        # Intentar cerrar
        response = instructor_client.post(
            "/api/subjects/instructor/close/",
            {"subject_id": subject.id}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["closed"] is False
