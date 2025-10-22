"""
Módulo de servicios para gestión de materias e inscripciones.

Este módulo contiene la lógica de negocio para:
- Validación de inscripciones de estudiantes
- Gestión de calificaciones
- Consultas de historial académico
- Asignación de instructores a materias
"""

from decimal import Decimal
from django.db.models import Avg
from .models import Subject, Enrollment


def can_enroll(user, subject_id):
    """
    Valida si un estudiante puede inscribirse en una materia.

    Args:
        user (User): El usuario estudiante
        subject_id (int): ID de la materia

    Returns:
        tuple: (bool, str) - (es_permitida_inscripcion, mensaje_razon)

    Validaciones realizadas:
        1. El usuario debe tener rol 'student'
        2. No puede estar ya inscrito o haber aprobado la materia
        3. Debe cumplir con todos los prerrequisitos
        4. No puede exceder el máximo de créditos por semestre
    """
    if not user.role or user.role.name != "student":
        return False, "not authorized"

    subject = Subject.objects.get(id=subject_id)

    if Enrollment.objects.filter(student=user, subject=subject, state__in=["approved","enrolled","closed"]).exists():
        return False, "already taken or enrolled"

    prerequisites = subject.prerequisites.all()
    approved_subjects = set(Enrollment.objects.filter(student=user, state="approved").values_list("subject_id", flat=True))

    for prerequisite in prerequisites:
        if prerequisite.id not in approved_subjects:
            return False, "missing prerequisites"

    max_credits = user.student.max_credits_per_term if hasattr(user, "student") else 0
    current_enrollments = Enrollment.objects.filter(student=user, state="enrolled").select_related("subject")
    credits_used = sum([enrollment.subject.credits for enrollment in current_enrollments])

    if credits_used + subject.credits > max_credits:
        return False, "credits exceeded"

    return True, "ok"


def enroll(user, subject_id):
    """
    Inscribe un estudiante en una materia.

    Args:
        user (User): El usuario estudiante a inscribir
        subject_id (int): ID de la materia

    Returns:
        Enrollment: El registro de inscripción creado o existente
    """
    subject = Subject.objects.get(id=subject_id)
    enrollment, _ = Enrollment.objects.get_or_create(
        student=user,
        subject=subject,
        defaults={"state": "enrolled"}
    )
    return enrollment


def enrolled_subjects(user):
    """
    Obtiene todas las materias en las que el estudiante está actualmente inscrito.

    Args:
        user (User): El usuario estudiante

    Returns:
        QuerySet[Enrollment]: Inscripciones en estado 'enrolled'
    """
    return Enrollment.objects.filter(student=user, state="enrolled").select_related("subject")


def approved_subjects(user):
    """
    Obtiene todas las materias que el estudiante ha aprobado.

    Args:
        user (User): El usuario estudiante

    Returns:
        QuerySet[Enrollment]: Inscripciones en estado 'approved'
    """
    return Enrollment.objects.filter(student=user, state="approved").select_related("subject")


def failed_subjects(user):
    """
    Obtiene todas las materias que el estudiante ha reprobado.

    Args:
        user (User): El usuario estudiante

    Returns:
        QuerySet[Enrollment]: Inscripciones en estado 'failed'
    """
    return Enrollment.objects.filter(student=user, state="failed").select_related("subject")


def gpa(user):
    """
    Calcula el promedio general (GPA) del estudiante.

    Args:
        user (User): El usuario estudiante

    Returns:
        Decimal: Promedio de todas las materias calificadas. Retorna 0.0 si no hay calificaciones.
    """
    enrolled_with_grades = Enrollment.objects.filter(student=user).exclude(grade__isnull=True)

    if not enrolled_with_grades.exists():
        return Decimal("0.0")

    return enrolled_with_grades.aggregate(avg=Avg("grade"))["avg"] or Decimal("0.0")


def history(user):
    """
    Obtiene el historial completo académico del estudiante.

    Args:
        user (User): El usuario estudiante

    Returns:
        QuerySet[Enrollment]: Todas las inscripciones ordenadas por fecha de creación
    """
    return Enrollment.objects.filter(student=user).select_related("subject").order_by("created_at")


def students_by_subject(instructor, subject_id):
    """
    Obtiene todos los estudiantes inscritos en una materia específica del profesor.

    Args:
        instructor (User): El usuario instructor
        subject_id (int): ID de la materia

    Returns:
        QuerySet[Enrollment]: Inscripciones de estudiantes en esa materia enseñada por el instructor
    """
    return Enrollment.objects.filter(subject_id=subject_id, subject__assigned_instructor=instructor)


def grade(instructor, enrollment_id, value):
    """
    Asigna una calificación a un estudiante en una materia.

    Args:
        instructor (User): El profesor que califica
        enrollment_id (int): ID de la inscripción
        value (float): Calificación numérica (0.0 a 5.0)

    Returns:
        Enrollment: La inscripción actualizada con la calificación

    Raises:
        ValueError: Si la calificación está fuera del rango [0.0, 5.0]
        Enrollment.DoesNotExist: Si la inscripción no existe o no pertenece a este profesor

    Comportamiento:
        - Calificación >= 3.0: Estado cambia a 'approved'
        - Calificación < 3.0: Estado cambia a 'failed'
        - Se crea una notificación para el estudiante
    """
    if value < 0 or value > 5:
        raise ValueError("invalid range")

    enrollment = Enrollment.objects.select_related("subject").get(
        id=enrollment_id,
        subject__assigned_instructor=instructor
    )

    enrollment.grade = round(Decimal(value), 1)
    enrollment.state = "approved" if enrollment.grade >= 3 else "failed"
    enrollment.save()

    from notifications.models import Notification
    Notification.objects.create(
        user=enrollment.student,
        type="grade",
        message=f"Grade {enrollment.grade} in {enrollment.subject.name}"
    )

    return enrollment


def close_subject(instructor, subject_id):
    """
    Cierra una materia después de que todos los estudiantes han sido calificados.

    Args:
        instructor (User): El profesor que cierra la materia
        subject_id (int): ID de la materia

    Returns:
        bool: True si la materia fue cerrada exitosamente, False en caso contrario

    Precondiciones:
        - Todos los estudiantes inscritos deben tener una calificación asignada
        - El instructor debe ser el profesor asignado a la materia

    Efecto:
        - Cambia el estado de todas las inscripciones a 'closed'
    """
    enrollments = Enrollment.objects.filter(subject_id=subject_id, subject__assigned_instructor=instructor)

    if not enrollments.exists():
        return False

    if enrollments.filter(grade__isnull=True).exists():
        return False

    enrollments.update(state="closed")
    return True


def assign_instructor(subject_id, instructor_user_id):
    """
    Asigna un profesor a una materia.

    Args:
        subject_id (int): ID de la materia
        instructor_user_id (int): ID del usuario con rol 'instructor'

    Returns:
        Subject: La materia actualizada con el instructor asignado

    Raises:
        Subject.DoesNotExist: Si la materia no existe
        User.DoesNotExist: Si el usuario no existe o no tiene rol 'instructor'
    """
    from accounts.models import User, Role

    subject = Subject.objects.get(id=subject_id)
    instructor_role = Role.objects.get(name="instructor")
    instructor = User.objects.get(id=instructor_user_id, role=instructor_role)

    subject.assigned_instructor = instructor
    subject.save()

    return subject
