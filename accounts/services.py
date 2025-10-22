"""
Módulo de servicios para gestión de usuarios y roles.

Este módulo proporciona funciones de negocio para:
- Asignación de roles a usuarios
- Cálculo de estadísticas del sistema académico
"""

from .models import User, Student, Instructor, Role
from django.db.models import Avg
from decimal import Decimal


def assign_role(user_id, role_name):
    """
    Asigna un rol a un usuario y crea los perfiles asociados si es necesario.

    Args:
        user_id (int): ID del usuario al que se le asignará el rol
        role_name (str): Nombre del rol ('admin', 'instructor', 'student')

    Returns:
        User: El usuario actualizado con el nuevo rol

    Raises:
        User.DoesNotExist: Si el usuario no existe
        Role.DoesNotExist: Si el rol especificado no existe

    Comportamiento:
        - Si el rol es 'student' y no existe perfil Student, lo crea
        - Si el rol es 'instructor' y no existe perfil Instructor, lo crea
    """
    from django.shortcuts import get_object_or_404

    user = User.objects.get(id=user_id)
    role_obj = get_object_or_404(Role, name=role_name)
    user.role = role_obj
    user.save()

    if role_name == "student" and not hasattr(user, "student"):
        Student.objects.create(user=user)
    if role_name == "instructor" and not hasattr(user, "instructor"):
        Instructor.objects.create(user=user)

    return user


def get_admin_statistics():
    """
    Calcula estadísticas completas del sistema académico para administradores.

    Returns:
        dict: Diccionario con las siguientes claves:
            - users: Conteos por rol y estado de actividad
            - subjects: Información sobre materias y profesores asignados
            - enrollments: Inscripciones distribuidas por estado
            - academic_performance: Tasas de aprobación, promedio general
            - grade_distribution: Distribución de calificaciones por rangos
            - professors_with_assignments: Total de profesores con asignaturas

    Cálculos realizados:
        - Conteo de usuarios por rol (admin, instructor, student)
        - Estudiantes activos (con al menos una inscripción)
        - Inscripciones agrupadas por estado (enrolled, approved, failed, closed)
        - Tasas de aprobación/reprobación (solo de inscritos completados)
        - Promedio de calificaciones del sistema
        - Promedio de calificaciones por estudiante
        - Distribución de notas en rangos: [0-1), [1-2), [2-3), [3-4), [4-5]
    """
    from subjects.models import Subject, Enrollment

    total_students = User.objects.filter(role__name="student").count()
    total_instructors = User.objects.filter(role__name="instructor").count()
    total_admins = User.objects.filter(role__name="admin").count()

    total_subjects = Subject.objects.count()
    subjects_with_instructor = Subject.objects.filter(assigned_instructor__isnull=False).count()
    subjects_without_instructor = total_subjects - subjects_with_instructor

    total_enrollments = Enrollment.objects.count()
    enrollments_enrolled = Enrollment.objects.filter(state="enrolled").count()
    enrollments_approved = Enrollment.objects.filter(state="approved").count()
    enrollments_failed = Enrollment.objects.filter(state="failed").count()
    enrollments_closed = Enrollment.objects.filter(state="closed").count()

    closed_enrollments = Enrollment.objects.filter(state__in=["approved", "failed"])
    total_closed = closed_enrollments.count()

    if total_closed > 0:
        approval_rate = (closed_enrollments.filter(state="approved").count() / total_closed) * 100
        failure_rate = (closed_enrollments.filter(state="failed").count() / total_closed) * 100
    else:
        approval_rate = 0
        failure_rate = 0

    avg_grade_result = Enrollment.objects.filter(grade__isnull=False).aggregate(avg=Avg("grade"))
    avg_grade = avg_grade_result["avg"] or Decimal("0.0")

    graded_enrollments = Enrollment.objects.filter(grade__isnull=False)
    grade_distribution = {
        "0_1": graded_enrollments.filter(grade__lt=1).count(),
        "1_2": graded_enrollments.filter(grade__gte=1, grade__lt=2).count(),
        "2_3": graded_enrollments.filter(grade__gte=2, grade__lt=3).count(),
        "3_4": graded_enrollments.filter(grade__gte=3, grade__lt=4).count(),
        "4_5": graded_enrollments.filter(grade__gte=4, grade__lte=5).count(),
    }

    professors_with_assignments = Subject.objects.filter(
        assigned_instructor__isnull=False
    ).values('assigned_instructor').distinct().count()

    avg_subjects_per_instructor = (total_subjects / professors_with_assignments) if professors_with_assignments > 0 else 0

    active_students = User.objects.filter(
        role__name="student",
        student_enrollments__isnull=False
    ).distinct().count()

    inactive_students = total_students - active_students

    student_gpas = []
    students = User.objects.filter(role__name="student")
    for student in students:
        enrollments = student.student_enrollments.filter(grade__isnull=False)
        if enrollments.exists():
            avg = enrollments.aggregate(avg=Avg("grade"))["avg"]
            student_gpas.append(float(avg) if avg else 0)

    avg_student_gpa = sum(student_gpas) / len(student_gpas) if student_gpas else 0

    statistics = {
        "users": {
            "total_students": total_students,
            "total_instructors": total_instructors,
            "total_admins": total_admins,
            "active_students": active_students,
            "inactive_students": inactive_students,
        },
        "subjects": {
            "total_subjects": total_subjects,
            "subjects_with_instructor": subjects_with_instructor,
            "subjects_without_instructor": subjects_without_instructor,
            "avg_subjects_per_instructor": round(avg_subjects_per_instructor, 2),
        },
        "enrollments": {
            "total_enrollments": total_enrollments,
            "enrollments_enrolled": enrollments_enrolled,
            "enrollments_approved": enrollments_approved,
            "enrollments_failed": enrollments_failed,
            "enrollments_closed": enrollments_closed,
        },
        "academic_performance": {
            "approval_rate": round(approval_rate, 2),
            "failure_rate": round(failure_rate, 2),
            "system_average_grade": round(float(avg_grade), 2),
            "average_student_gpa": round(avg_student_gpa, 2),
        },
        "grade_distribution": grade_distribution,
        "professors_with_assignments": professors_with_assignments,
    }

    return statistics
