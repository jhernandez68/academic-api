"""
Configuración global de pytest y fixtures compartidas.

Este archivo define:
- Fixtures para crear usuarios, roles, materias y inscripciones
- Fixtures para cliente autenticado (JWT)
- Configuración de base de datos de prueba
- Factories para generar datos de prueba
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Role, Student, Instructor
from subjects.models import Subject, Enrollment
from notifications.models import Notification

User = get_user_model()


# ============================================================================
# FIXTURES DE ROLES
# ============================================================================

@pytest.fixture
def admin_role(db):
    """Crea el rol de administrador."""
    role, _ = Role.objects.get_or_create(
        name="admin",
        defaults={"display_name": "Administrador", "description": "Rol de administrador"}
    )
    return role


@pytest.fixture
def instructor_role(db):
    """Crea el rol de instructor."""
    role, _ = Role.objects.get_or_create(
        name="instructor",
        defaults={"display_name": "Instructor", "description": "Rol de instructor"}
    )
    return role


@pytest.fixture
def student_role(db):
    """Crea el rol de estudiante."""
    role, _ = Role.objects.get_or_create(
        name="student",
        defaults={"display_name": "Estudiante", "description": "Rol de estudiante"}
    )
    return role


# ============================================================================
# FIXTURES DE USUARIOS
# ============================================================================

@pytest.fixture
def admin_user(db, admin_role):
    """Obtiene o crea un usuario administrador autenticado."""
    user, _ = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User",
            "role": admin_role
        }
    )
    # Asegurar que tiene el rol correcto
    if user.role != admin_role:
        user.role = admin_role
        user.save()
    return user


@pytest.fixture
def instructor_user(db, instructor_role):
    """Obtiene o crea un usuario instructor autenticado."""
    user, _ = User.objects.get_or_create(
        username="instructor",
        defaults={
            "email": "instructor@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": instructor_role
        }
    )
    if user.role != instructor_role:
        user.role = instructor_role
        user.save()

    # Asegurar que tiene perfil de instructor con max_credits
    from accounts.models import Instructor
    Instructor.objects.get_or_create(
        user=user,
        defaults={"max_credits_per_term": 20}
    )

    return user


@pytest.fixture
def student_user(db, student_role):
    """Obtiene o crea un usuario estudiante autenticado."""
    user, _ = User.objects.get_or_create(
        username="student",
        defaults={
            "email": "student@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "role": student_role
        }
    )
    if user.role != student_role:
        user.role = student_role
        user.save()

    # Asegurar que tiene perfil de estudiante con max_credits
    from accounts.models import Student
    Student.objects.get_or_create(
        user=user,
        defaults={"max_credits_per_term": 16}
    )

    return user


@pytest.fixture
def multiple_students(db, student_role):
    """Crea múltiples estudiantes para pruebas."""
    students = []
    for i in range(3):
        user = User.objects.create_user(
            username=f"student{i}",
            email=f"student{i}@example.com",
            password="student123",
            role=student_role
        )
        students.append(user)
    return students


# ============================================================================
# FIXTURES DE MATERIAS
# ============================================================================

@pytest.fixture
def subject_without_prerequisites(db, instructor_user):
    """Crea una materia sin prerequisitos."""
    subject, _ = Subject.objects.get_or_create(
        code="MAT101",
        defaults={
            "name": "Mathematics 101",
            "credits": 4,
            "assigned_instructor": instructor_user
        }
    )
    return subject


@pytest.fixture
def subject_with_prerequisites(db, instructor_user, subject_without_prerequisites):
    """Crea una materia que requiere prerequisitos."""
    subject, created = Subject.objects.get_or_create(
        code="MAT201",
        defaults={
            "name": "Advanced Mathematics",
            "credits": 4,
            "assigned_instructor": instructor_user
        }
    )
    if created or not subject.prerequisites.exists():
        subject.prerequisites.add(subject_without_prerequisites)
    return subject


@pytest.fixture
def multiple_subjects(db, instructor_user):
    """Crea múltiples materias."""
    subjects = []
    for i in range(5):
        subject = Subject.objects.create(
            name=f"Subject {i}",
            code=f"SUB{i:03d}",
            credits=3 + (i % 2),
            assigned_instructor=instructor_user
        )
        subjects.append(subject)
    return subjects


# ============================================================================
# FIXTURES DE INSCRIPCIONES
# ============================================================================

@pytest.fixture
def enrollment(db, student_user, subject_without_prerequisites):
    """Crea una inscripción de estudiante en una materia."""
    enrollment, _ = Enrollment.objects.get_or_create(
        student=student_user,
        subject=subject_without_prerequisites,
        defaults={
            "state": "enrolled",
            "grade": None
        }
    )
    return enrollment


@pytest.fixture
def graded_enrollment(db, student_user, subject_with_prerequisites):
    """Crea una inscripción calificada como aprobada."""
    enrollment, _ = Enrollment.objects.get_or_create(
        student=student_user,
        subject=subject_with_prerequisites,
        defaults={
            "state": "approved",
            "grade": Decimal("4.5")
        }
    )
    return enrollment


@pytest.fixture
def failed_enrollment(db, student_user, instructor_user):
    """Crea una inscripción calificada como reprobada."""
    # Crear una materia específica para este fixture
    failed_subject, _ = Subject.objects.get_or_create(
        code="FAILED001",
        defaults={
            "name": "Failed Subject",
            "credits": 3,
            "assigned_instructor": instructor_user
        }
    )
    enrollment, _ = Enrollment.objects.get_or_create(
        student=student_user,
        subject=failed_subject,
        defaults={
            "state": "failed",
            "grade": Decimal("2.0")
        }
    )
    return enrollment


# ============================================================================
# FIXTURES DE NOTIFICACIONES
# ============================================================================

@pytest.fixture
def notification(db, student_user):
    """Crea una notificación."""
    notification = Notification.objects.create(
        user=student_user,
        type="enrollment",
        message="You have been enrolled in a new subject",
        is_read=False
    )
    return notification


@pytest.fixture
def read_notification(db, student_user):
    """Crea una notificación leída."""
    notification = Notification.objects.create(
        user=student_user,
        type="grade",
        message="Your grade has been updated",
        is_read=True
    )
    return notification


# ============================================================================
# FIXTURES DE CLIENTE API
# ============================================================================

@pytest.fixture
def api_client():
    """Retorna un cliente API sin autenticación."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, student_user):
    """Retorna un cliente API autenticado como estudiante."""
    refresh = RefreshToken.for_user(student_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def instructor_client(api_client, instructor_user):
    """Retorna un cliente API autenticado como instructor."""
    refresh = RefreshToken.for_user(instructor_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Retorna un cliente API autenticado como admin."""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


# ============================================================================
# FIXTURES DE DATOS COMPLETOS
# ============================================================================

@pytest.fixture
def complete_scenario(db, admin_user, instructor_user, student_user,
                     subject_without_prerequisites, enrollment):
    """Crea un escenario completo con usuario, materia e inscripción."""
    return {
        "admin": admin_user,
        "instructor": instructor_user,
        "student": student_user,
        "subject": subject_without_prerequisites,
        "enrollment": enrollment
    }
