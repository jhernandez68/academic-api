"""
Serializadores para la gestión de materias e inscripciones.

Este módulo contiene los serializadores (serializers) utilizados para
serializar/deserializar datos de materias e inscripciones entre la API REST y los modelos Django.

Serializadores:
    - AssignInstructorSerializer: Datos para asignar un instructor a una materia
    - SubjectSerializer: Serialización completa del modelo Subject
    - EnrollmentSerializer: Serialización del modelo Enrollment
"""

from rest_framework import serializers
from .models import Subject, Enrollment

class AssignInstructorSerializer(serializers.Serializer):
    """
    Serializador para asignación de instructores a materias.

    Se utiliza en el endpoint POST /subjects/{id}/assign_instructor/

    Campos:
        instructor_user_id (int): ID del usuario con rol 'instructor' que se asignará a la materia

    Ejemplo de entrada:
        {
            "instructor_user_id": 5
        }
    """
    instructor_user_id = serializers.IntegerField(help_text="ID del usuario instructor")

class SubjectSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Subject.

    Se utiliza para serializar materias del programa académico.

    Campos:
        id (int): Identificador único de la materia
        name (str): Nombre de la materia
        code (str): Código único de la materia (ej: MAT101)
        credits (int): Número de créditos de la materia
        assigned_instructor (int/object): ID o datos del profesor asignado (puede ser null)
        prerequisites (list): Lista de IDs de materias que son prerrequisitos

    Nota:
        - El código de la materia es único en el sistema
        - Una materia puede no tener instructor asignado (assigned_instructor=null)
        - Los prerrequisitos son materias que deben aprobarse antes de esta
    """
    class Meta:
        model = Subject
        fields = ["id","name","code","credits","assigned_instructor","prerequisites"]

class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Enrollment.

    Se utiliza para serializar inscripciones de estudiantes en materias.

    Campos de lectura:
        id (int): Identificador único de la inscripción
        state (str): Estado actual de la inscripción (enrolled, approved, failed, closed)
        grade (decimal): Calificación numérica (0.0 a 5.0), null si sin calificar
        created_at (datetime): Fecha y hora de inscripción
        student (int): ID del estudiante inscrito

    Campos de escritura:
        subject (int): ID de la materia en la que inscribirse

    Campos de solo lectura:
        state: Determinado automáticamente según la calificación (read-only)
        grade: Solo modificable por instructores (read-only)
        student: Se obtiene del usuario autenticado (read-only)

    Estados posibles:
        - 'enrolled': Estudiante actualmente cursando la materia
        - 'approved': Materia aprobada (calificación >= 3.0)
        - 'failed': Materia reprobada (calificación < 3.0)
        - 'closed': Materia cerrada por el instructor

    Nota:
        - Las inscripciones no pueden duplicarse (constraint unique_together en model)
        - Solo el profesor asignado puede calificar
    """
    grade = serializers.SerializerMethodField()

    def get_grade(self, obj):
        """Convierte Decimal a float para una mejor serialización JSON."""
        if obj.grade is None:
            return None
        return float(obj.grade)

    class Meta:
        model = Enrollment
        fields = ["id","student","subject","state","grade","created_at"]
        read_only_fields = ["state","grade","student"]
