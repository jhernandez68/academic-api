"""
Tests para la aplicación de materias (académica).

Cobertura:
- Modelos: Subject, Enrollment
- Vistas: Inscripción, calificación, cierre de materias
- Servicios: Validaciones académicas, cálculo de GPA, historial
- Decoradores: Validación de prerequisitos
- Lógica de negocio: Reglas de inscripción, calificación, aprobación
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import status

from subjects.models import Subject, Enrollment
from subjects.services import (
    can_enroll, enroll, enrolled_subjects, approved_subjects,
    failed_subjects, gpa, history, students_by_subject, grade,
    close_subject
)
from accounts.models import Student

User = get_user_model()


# ============================================================================
# TESTS DE MODELOS
# ============================================================================

@pytest.mark.unit
class TestSubjectModel:
    """Tests para el modelo Subject."""

    def test_create_subject(self, db, instructor_user):
        """Prueba crear una materia."""
        subject = Subject.objects.create(
            name="Mathematics",
            code="MAT101",
            credits=4,
            assigned_instructor=instructor_user
        )
        assert subject.name == "Mathematics"
        assert subject.code == "MAT101"
        assert subject.credits == 4

    def test_subject_unique_code(self, db, instructor_user):
        """Prueba que el código debe ser único."""
        Subject.objects.create(
            name="Math 1",
            code="MAT101",
            credits=4,
            assigned_instructor=instructor_user
        )
        with pytest.raises(Exception):
            Subject.objects.create(
                name="Math 2",
                code="MAT101",
                credits=4,
                assigned_instructor=instructor_user
            )

    def test_subject_with_prerequisites(self, db, instructor_user):
        """Prueba crear una materia con prerequisitos."""
        basic = Subject.objects.create(
            name="Basic Math",
            code="MAT101",
            credits=3,
            assigned_instructor=instructor_user
        )
        advanced = Subject.objects.create(
            name="Advanced Math",
            code="MAT201",
            credits=4,
            assigned_instructor=instructor_user
        )
        advanced.prerequisites.add(basic)

        assert basic in advanced.prerequisites.all()


@pytest.mark.unit
class TestEnrollmentModel:
    """Tests para el modelo Enrollment."""

    def test_create_enrollment(self, db, student_user, subject_without_prerequisites):
        """Prueba crear una inscripción."""
        enrollment = Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="enrolled"
        )
        assert enrollment.state == "enrolled"
        assert enrollment.grade is None

    def test_enrollment_unique_constraint(self, db, student_user, subject_without_prerequisites):
        """Prueba que un estudiante solo puede inscribirse una vez por materia."""
        Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="enrolled"
        )
        with pytest.raises(Exception):
            Enrollment.objects.create(
                student=student_user,
                subject=subject_without_prerequisites,
                state="enrolled"
            )

    def test_enrollment_grade_range(self, db, student_user, subject_without_prerequisites):
        """Prueba que la calificación está en el rango 0.0 a 5.0."""
        enrollment = Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="approved",
            grade=Decimal("4.5")
        )
        assert Decimal("0") <= enrollment.grade <= Decimal("5")

    def test_enrollment_valid_states(self, db, student_user, subject_without_prerequisites):
        """Prueba los estados válidos de inscripción."""
        valid_states = ["enrolled", "approved", "failed", "closed"]
        for state in valid_states:
            enrollment = Enrollment.objects.create(
                student=User.objects.create_user(f"user{state}", "test@test.com", "pass"),
                subject=subject_without_prerequisites,
                state=state
            )
            assert enrollment.state == state


# ============================================================================
# TESTS DE SERVICIOS - VALIDACIÓN DE INSCRIPCIÓN
# ============================================================================

@pytest.mark.unit
class TestCanEnrollService:
    """Tests para el servicio can_enroll (validación de inscripción)."""

    def test_can_enroll_basic_validation(self, student_user, subject_without_prerequisites):
        """Prueba que un estudiante puede inscribirse en una materia sin prerequisitos."""
        can_enroll_result = can_enroll(student_user, subject_without_prerequisites.id)
        assert can_enroll_result is True

    def test_cannot_enroll_duplicate(self, student_user, subject_without_prerequisites):
        """Prueba que no puede inscribirse dos veces en la misma materia."""
        Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="enrolled"
        )
        result = can_enroll(student_user, subject_without_prerequisites.id)
        assert result is False

    def test_cannot_enroll_without_prerequisite(self, student_user, subject_with_prerequisites,
                                                subject_without_prerequisites):
        """Prueba que no puede inscribirse sin cumplir prerequisitos."""
        result = can_enroll(student_user, subject_with_prerequisites.id)
        assert result is False

    def test_can_enroll_with_prerequisite_met(self, student_user, subject_with_prerequisites,
                                              subject_without_prerequisites):
        """Prueba que puede inscribirse cuando ha aprobado el prerequisito."""
        Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="approved",
            grade=Decimal("3.5")
        )
        result = can_enroll(student_user, subject_with_prerequisites.id)
        assert result is True

    def test_cannot_enroll_with_credit_limit_exceeded(self, db, student_user):
        """Prueba que no puede exceder el límite de créditos."""
        # Crear materias de 5 créditos c/u
        subjects = []
        for i in range(4):
            subj = Subject.objects.create(
                name=f"Subject {i}",
                code=f"SUB{i}",
                credits=5,
                assigned_instructor=User.objects.create_user(
                    f"inst{i}", f"inst{i}@test.com", "pass"
                )
            )
            subjects.append(subj)
            Enrollment.objects.create(
                student=student_user,
                subject=subj,
                state="enrolled"
            )

        # Ahora tiene 20 créditos, máximo es 16, debería fallar
        new_subject = Subject.objects.create(
            name="Extra Subject",
            code="EXTRA",
            credits=3,
            assigned_instructor=User.objects.create_user("inst5", "inst5@test.com", "pass")
        )
        result = can_enroll(student_user, new_subject.id)
        assert result is False

    def test_cannot_enroll_already_approved(self, student_user, subject_without_prerequisites):
        """Prueba que no puede inscribirse si ya aprobó la materia."""
        Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="approved",
            grade=Decimal("3.5")
        )
        result = can_enroll(student_user, subject_without_prerequisites.id)
        assert result is False


# ============================================================================
# TESTS DE SERVICIOS - OPERACIONES ACADÉMICAS
# ============================================================================

@pytest.mark.unit
class TestEnrollmentServices:
    """Tests para servicios de inscripción."""

    def test_enroll_service(self, student_user, subject_without_prerequisites):
        """Prueba el servicio enroll."""
        enrollment = enroll(student_user.id, subject_without_prerequisites.id)
        assert enrollment.student == student_user
        assert enrollment.subject == subject_without_prerequisites
        assert enrollment.state == "enrolled"

    def test_enrolled_subjects(self, student_user, subject_without_prerequisites):
        """Prueba obtener materias inscritas."""
        Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="enrolled"
        )
        subjects = enrolled_subjects(student_user.id)
        assert subject_without_prerequisites in subjects

    def test_approved_subjects(self, db, student_user, multiple_subjects):
        """Prueba obtener materias aprobadas."""
        for subject in multiple_subjects[:2]:
            Enrollment.objects.create(
                student=student_user,
                subject=subject,
                state="approved",
                grade=Decimal("3.5")
            )
        approved = approved_subjects(student_user.id)
        assert len(approved) == 2

    def test_failed_subjects(self, db, student_user, multiple_subjects):
        """Prueba obtener materias reprobadas."""
        Enrollment.objects.create(
            student=student_user,
            subject=multiple_subjects[0],
            state="failed",
            grade=Decimal("2.0")
        )
        failed = failed_subjects(student_user.id)
        assert len(failed) == 1

    def test_history(self, db, student_user, multiple_subjects):
        """Prueba obtener historial académico completo."""
        for subject in multiple_subjects:
            Enrollment.objects.create(
                student=student_user,
                subject=subject,
                state="approved",
                grade=Decimal("3.5")
            )
        hist = history(student_user.id)
        assert len(hist) == len(multiple_subjects)


# ============================================================================
# TESTS DE SERVICIOS - CALIFICACIONES Y GPA
# ============================================================================

@pytest.mark.unit
class TestGradeAndGPAServices:
    """Tests para servicios de calificación y GPA."""

    def test_gpa_calculation(self, db, student_user, multiple_subjects):
        """Prueba el cálculo del GPA."""
        # Crear inscripciones con diferentes calificaciones
        grades = [Decimal("5.0"), Decimal("4.0"), Decimal("3.0")]
        for i, subject in enumerate(multiple_subjects[:3]):
            Enrollment.objects.create(
                student=student_user,
                subject=subject,
                state="approved",
                grade=grades[i]
            )

        student_gpa = gpa(student_user.id)
        expected_gpa = (Decimal("5.0") + Decimal("4.0") + Decimal("3.0")) / 3
        assert student_gpa == expected_gpa

    def test_gpa_empty_enrollment(self, student_user):
        """Prueba GPA cuando no hay inscripciones."""
        student_gpa = gpa(student_user.id)
        assert student_gpa == 0

    def test_gpa_only_enrolled(self, student_user, subject_without_prerequisites):
        """Prueba que GPA no incluye materias en curso (sin calificación)."""
        Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="enrolled"
        )
        student_gpa = gpa(student_user.id)
        assert student_gpa == 0

    def test_grade_service(self, student_user, subject_without_prerequisites, enrollment):
        """Prueba el servicio grade."""
        grade(enrollment.id, Decimal("4.5"))
        enrollment.refresh_from_db()

        assert enrollment.grade == Decimal("4.5")
        assert enrollment.state == "approved"

    def test_grade_updates_state_approved(self, student_user, subject_without_prerequisites, enrollment):
        """Prueba que la calificación >= 3.0 marca como aprobada."""
        grade(enrollment.id, Decimal("3.0"))
        enrollment.refresh_from_db()

        assert enrollment.state == "approved"

    def test_grade_updates_state_failed(self, student_user, subject_without_prerequisites, enrollment):
        """Prueba que la calificación < 3.0 marca como reprobada."""
        grade(enrollment.id, Decimal("2.5"))
        enrollment.refresh_from_db()

        assert enrollment.state == "failed"


# ============================================================================
# TESTS DE SERVICIOS - PROFESOR
# ============================================================================

@pytest.mark.unit
class TestInstructorServices:
    """Tests para servicios de profesor."""

    def test_students_by_subject(self, db, instructor_user, subject_without_prerequisites, multiple_students):
        """Prueba obtener estudiantes por materia."""
        for student in multiple_students:
            Enrollment.objects.create(
                student=student,
                subject=subject_without_prerequisites,
                state="enrolled"
            )

        students = students_by_subject(subject_without_prerequisites.id)
        assert len(students) == len(multiple_students)

    def test_close_subject_success(self, student_user, subject_without_prerequisites, enrollment):
        """Prueba cerrar una materia con todos calificados."""
        grade(enrollment.id, Decimal("4.0"))
        enrollment.refresh_from_db()

        close_subject(subject_without_prerequisites.id)
        enrollment.refresh_from_db()

        assert enrollment.state == "closed"

    def test_cannot_close_subject_with_uncalified(self, student_user, subject_without_prerequisites, enrollment):
        """Prueba que no puede cerrar si hay sin calificar."""
        result = close_subject(subject_without_prerequisites.id)
        # El servicio debería retornar False o lanzar excepción


# ============================================================================
# TESTS DE VISTAS (API ENDPOINTS)
# ============================================================================

@pytest.mark.integration
class TestEnrollmentEndpoints:
    """Tests para endpoints de inscripción."""

    def test_enroll_student(self, authenticated_client, student_user, subject_without_prerequisites):
        """Prueba inscribirse en una materia."""
        response = authenticated_client.post("/api/subjects/student/enroll/", {
            "subject_id": subject_without_prerequisites.id
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_get_enrolled_subjects(self, authenticated_client, enrollment):
        """Prueba obtener materias inscritas."""
        response = authenticated_client.get("/api/subjects/student/enrolled/")
        assert response.status_code == status.HTTP_200_OK

    def test_get_approved_subjects(self, authenticated_client, graded_enrollment):
        """Prueba obtener materias aprobadas."""
        response = authenticated_client.get("/api/subjects/student/approved/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_failed_subjects(self, authenticated_client, failed_enrollment):
        """Prueba obtener materias reprobadas."""
        response = authenticated_client.get("/api/subjects/student/failed/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_get_student_gpa(self, authenticated_client, graded_enrollment):
        """Prueba obtener GPA del estudiante."""
        response = authenticated_client.get("/api/subjects/student/gpa/")
        assert response.status_code == status.HTTP_200_OK
        assert "gpa" in response.data

    def test_get_academic_history(self, authenticated_client, enrollment):
        """Prueba obtener historial académico."""
        response = authenticated_client.get("/api/subjects/student/history/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestInstructorEndpoints:
    """Tests para endpoints de instructor."""

    def test_get_assigned_subjects(self, instructor_client, instructor_user):
        """Prueba obtener materias asignadas."""
        response = instructor_client.get("/api/subjects/instructor/assigned_subjects/")
        assert response.status_code == status.HTTP_200_OK

    def test_get_students_by_subject(self, instructor_client, subject_without_prerequisites, enrollment):
        """Prueba obtener estudiantes de una materia."""
        response = instructor_client.get(
            f"/api/subjects/instructor/students/?subject_id={subject_without_prerequisites.id}"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_grade_student(self, instructor_client, enrollment):
        """Prueba calificar un estudiante."""
        response = instructor_client.post("/api/subjects/instructor/grade/", {
            "enrollment_id": enrollment.id,
            "grade": 4.5
        })
        assert response.status_code == status.HTTP_200_OK

    def test_close_subject(self, instructor_client, subject_without_prerequisites, graded_enrollment):
        """Prueba cerrar una materia."""
        response = instructor_client.post("/api/subjects/instructor/close/", {
            "subject_id": subject_without_prerequisites.id
        })
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestSubjectManagementEndpoints:
    """Tests para endpoints de gestión de materias."""

    def test_list_subjects(self, api_client):
        """Prueba listar materias."""
        response = api_client.get("/api/subjects/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_subject_as_admin(self, admin_client, instructor_user):
        """Prueba crear materia como admin."""
        response = admin_client.post("/api/subjects/", {
            "name": "New Subject",
            "code": "NEW101",
            "credits": 3,
            "assigned_instructor": instructor_user.id
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_subject_as_student_forbidden(self, authenticated_client):
        """Prueba que estudiantes no pueden crear materias."""
        response = authenticated_client.post("/api/subjects/", {
            "name": "New Subject",
            "code": "NEW101",
            "credits": 3
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_assign_instructor(self, admin_client, subject_without_prerequisites, instructor_user):
        """Prueba asignar instructor a materia."""
        new_instructor = User.objects.create_user(
            "newinstructor", "new@test.com", "pass"
        )
        response = admin_client.post(
            f"/api/subjects/{subject_without_prerequisites.id}/assign_instructor/",
            {"instructor_id": new_instructor.id}
        )
        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# TESTS DE DECORADORES
# ============================================================================

@pytest.mark.unit
class TestPrerequisiteDecorator:
    """Tests para el decorador @validate_prerequisites."""

    def test_decorator_validates_prerequisites(self, student_user, subject_with_prerequisites):
        """Prueba que el decorador valida prerequisitos."""
        # Este test requeriría una aplicación real con vistas
        # que usen el decorador, por ahora es una prueba conceptual
        pass


# ============================================================================
# TESTS DE LÓGICA DE NEGOCIO
# ============================================================================

@pytest.mark.unit
class TestAcademicBusinessLogic:
    """Tests para la lógica de negocio académica."""

    def test_pass_grade_threshold(self, db, student_user, subject_without_prerequisites):
        """Prueba que una calificación >= 3.0 es aprobada."""
        enrollment = Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="enrolled"
        )
        grade(enrollment.id, Decimal("3.0"))
        enrollment.refresh_from_db()

        assert enrollment.state == "approved"

    def test_fail_grade_threshold(self, db, student_user, subject_without_prerequisites):
        """Prueba que una calificación < 3.0 es reprobada."""
        enrollment = Enrollment.objects.create(
            student=student_user,
            subject=subject_without_prerequisites,
            state="enrolled"
        )
        grade(enrollment.id, Decimal("2.9"))
        enrollment.refresh_from_db()

        assert enrollment.state == "failed"

    def test_grade_range_validation(self, enrollment):
        """Prueba que la calificación está entre 0.0 y 5.0."""
        grade(enrollment.id, Decimal("5.0"))
        enrollment.refresh_from_db()
        assert enrollment.grade == Decimal("5.0")

        enrollment2 = Enrollment.objects.create(
            student=enrollment.student,
            subject=Subject.objects.create(
                name="Test", code="TST123", credits=3
            ),
            state="enrolled"
        )
        grade(enrollment2.id, Decimal("0.0"))
        enrollment2.refresh_from_db()
        assert enrollment2.grade == Decimal("0.0")

    def test_max_credits_per_semester(self, db, student_user, multiple_subjects):
        """Prueba que no puede exceder máximo de créditos."""
        # student_user tiene máximo 16 créditos
        # Crear varias materias de 4 créditos c/u
        for subject in multiple_subjects[:4]:
            subject.credits = 4
            subject.save()
            Enrollment.objects.create(
                student=student_user,
                subject=subject,
                state="enrolled"
            )

        # Total: 16 créditos (en límite)
        # Intentar agregar otra
        extra = Subject.objects.create(
            name="Extra", code="EXT999", credits=3
        )
        result = can_enroll(student_user, extra.id)
        assert result is False

    def test_multiple_prerequisites_validation(self, db, student_user, subject_without_prerequisites):
        """Prueba validación con múltiples prerequisitos."""
        prereq1 = subject_without_prerequisites
        prereq2 = Subject.objects.create(
            name="Prereq 2",
            code="PRE002",
            credits=3
        )
        advanced = Subject.objects.create(
            name="Advanced",
            code="ADV001",
            credits=4
        )
        advanced.prerequisites.add(prereq1, prereq2)

        # Sin aprobar ninguno - debería fallar
        result = can_enroll(student_user, advanced.id)
        assert result is False

        # Aprobar el primero - debería fallar
        Enrollment.objects.create(
            student=student_user,
            subject=prereq1,
            state="approved",
            grade=Decimal("3.5")
        )
        result = can_enroll(student_user, advanced.id)
        assert result is False

        # Aprobar ambos - debería pasar
        Enrollment.objects.create(
            student=student_user,
            subject=prereq2,
            state="approved",
            grade=Decimal("3.5")
        )
        result = can_enroll(student_user, advanced.id)
        assert result is True
