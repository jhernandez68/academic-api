"""
Modelos para gestión de materias e inscripciones académicas.

Este módulo define:
- Subject: Representa una materia del programa académico
- Enrollment: Representa la inscripción de un estudiante en una materia
"""

from django.db import models
from accounts.models import User


class Subject(models.Model):
    """
    Representa una materia del programa académico.

    Atributos:
        name (CharField): Nombre de la materia
        code (CharField): Código único de la materia (ej: MAT101)
        credits (PositiveIntegerField): Número de créditos de la materia
        prerequisites (ManyToManyField): Materias que deben aprobarse antes de esta
        assigned_instructor (ForeignKey): Profesor asignado a la materia (puede ser null)
    """
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    credits = models.PositiveIntegerField()
    prerequisites = models.ManyToManyField("self", symmetrical=False, blank=True, related_name="required_by")
    assigned_instructor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_subjects"
    )


class Enrollment(models.Model):
    """
    Registro de inscripción de un estudiante en una materia.

    Representa la relación entre un estudiante y una materia, incluyendo su estado
    y calificación (si aplica).

    Atributos:
        student (ForeignKey): Usuario estudiante inscrito
        subject (ForeignKey): Materia en la que está inscrito
        state (CharField): Estado actual de la inscripción:
            - 'enrolled': Actualmente cursando
            - 'approved': Aprobó (calificación >= 3.0)
            - 'failed': Reprobó (calificación < 3.0)
            - 'closed': Materia finalizada por el profesor
        grade (DecimalField): Calificación numérica (0.0 a 5.0), null si no hay calificación
        created_at (DateTimeField): Fecha de inscripción

    Restricciones:
        - Un estudiante solo puede tener una inscripción por materia (unique_together)
    """

    STATES = [
        ("enrolled", "enrolled"),
        ("approved", "approved"),
        ("failed", "failed"),
        ("closed", "closed")
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_enrollments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="enrollments")
    state = models.CharField(max_length=20, choices=STATES, default="enrolled")
    grade = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "subject")
