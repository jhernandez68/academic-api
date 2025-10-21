from .models import User, Student, Instructor, Role
from django.db.models import Count, Avg, Q, DecimalField
from django.db.models.functions import Coalesce

def assign_role(user_id, role_name):
    """Asigna un rol a un usuario. El parámetro role_name debe ser el nombre del rol (admin, instructor, student)"""
    from django.shortcuts import get_object_or_404

    u = User.objects.get(id=user_id)
    role_obj = get_object_or_404(Role, name=role_name)
    u.role = role_obj
    u.save()

    if role_name == "student" and not hasattr(u, "student"):
        Student.objects.create(user=u)
    if role_name == "instructor" and not hasattr(u, "instructor"):
        Instructor.objects.create(user=u)

    return u


def get_admin_statistics():
    """
    Calcula y retorna estadísticas generales del sistema para administradores.
    Incluye información sobre usuarios, materias, inscripciones y desempeño académico.
    """
    from subjects.models import Subject, Enrollment

    # Contar usuarios por rol
    total_students = User.objects.filter(role__name="student").count()
    total_instructors = User.objects.filter(role__name="instructor").count()
    total_admins = User.objects.filter(role__name="admin").count()

    # Contar materias
    total_subjects = Subject.objects.count()
    subjects_with_instructor = Subject.objects.filter(assigned_instructor__isnull=False).count()
    subjects_without_instructor = total_subjects - subjects_with_instructor

    # Contar inscripciones totales
    total_enrollments = Enrollment.objects.count()

    # Contar inscripciones por estado
    enrollments_enrolled = Enrollment.objects.filter(state="enrolled").count()
    enrollments_approved = Enrollment.objects.filter(state="approved").count()
    enrollments_failed = Enrollment.objects.filter(state="failed").count()
    enrollments_closed = Enrollment.objects.filter(state="closed").count()

    # Calcular tasas de aprobación/reprobación (entre inscripciones cerradas)
    closed_enrollments = Enrollment.objects.filter(state__in=["approved", "failed"])
    total_closed = closed_enrollments.count()

    if total_closed > 0:
        approval_rate = (closed_enrollments.filter(state="approved").count() / total_closed) * 100
        failure_rate = (closed_enrollments.filter(state="failed").count() / total_closed) * 100
    else:
        approval_rate = 0
        failure_rate = 0

    # Calcular promedio general del sistema
    from decimal import Decimal
    avg_grade_result = Enrollment.objects.filter(
        grade__isnull=False
    ).aggregate(
        avg=Avg("grade")
    )
    avg_grade = avg_grade_result["avg"] or Decimal("0.0")

    # Distribución de calificaciones (solo las completadas)
    graded_enrollments = Enrollment.objects.filter(grade__isnull=False)
    grade_distribution = {
        "0_1": graded_enrollments.filter(grade__lt=1).count(),
        "1_2": graded_enrollments.filter(grade__gte=1, grade__lt=2).count(),
        "2_3": graded_enrollments.filter(grade__gte=2, grade__lt=3).count(),
        "3_4": graded_enrollments.filter(grade__gte=3, grade__lt=4).count(),
        "4_5": graded_enrollments.filter(grade__gte=4, grade__lte=5).count(),
    }

    # Estadísticas por profesor
    professors_with_assignments = Subject.objects.filter(
        assigned_instructor__isnull=False
    ).values('assigned_instructor').distinct().count()

    # Promedio de materias por profesor
    if professors_with_assignments > 0:
        avg_subjects_per_instructor = total_subjects / professors_with_assignments
    else:
        avg_subjects_per_instructor = 0

    # Estudiantes activos (con al menos una inscripción)
    active_students = User.objects.filter(
        role__name="student",
        student_enrollments__isnull=False
    ).distinct().count()

    inactive_students = total_students - active_students

    # Estudiantes por promedio
    student_gpas = []
    students = User.objects.filter(role__name="student")
    for student in students:
        enrollments = student.student_enrollments.filter(grade__isnull=False)
        if enrollments.exists():
            avg = enrollments.aggregate(avg=Avg("grade"))["avg"]
            student_gpas.append(float(avg) if avg else 0)

    avg_student_gpa = sum(student_gpas) / len(student_gpas) if student_gpas else 0

    # Compilar estadísticas
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
