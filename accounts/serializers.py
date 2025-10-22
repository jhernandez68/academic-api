"""
Serializadores para la gestión de usuarios y roles.

Este módulo contiene los serializadores (serializers) utilizados para
serializar/deserializar datos de usuarios entre la API REST y los modelos Django.

Serializadores:
    - AssignRoleSerializer: Datos para asignar un rol a un usuario
    - RoleSerializer: Serialización completa del modelo Role
    - UserSerializer: Serialización de usuarios para lectura
    - CreateUserSerializer: Serialización para creación de nuevos usuarios
    - AdminStatisticsSerializer: Serialización de estadísticas del sistema
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Student, Instructor, Role

class AssignRoleSerializer(serializers.Serializer):
    """
    Serializador para asignación de roles a usuarios.

    Se utiliza en el endpoint POST /users/{id}/assign_role/

    Campos:
        role (CharField): Nombre del rol a asignar ('admin', 'instructor' o 'student')

    Ejemplo de entrada:
        {
            "role": "student"
        }
    """
    role = serializers.CharField(help_text="Nombre del rol: 'admin', 'instructor' o 'student'")

class RoleSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Role.

    Serializa los datos básicos de un rol del sistema.

    Campos:
        id (int): Identificador único del rol
        name (str): Nombre único del rol ('admin', 'instructor', 'student')
        display_name (str): Nombre legible para mostrar en interfaces
    """
    class Meta:
        model = Role
        fields = ["id", "name", "display_name"]

class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para lectura de usuarios.

    Se utiliza para retornar información de usuarios en respuestas de la API.

    Campos:
        id (int): Identificador único del usuario
        username (str): Nombre único de usuario
        email (str): Dirección de correo electrónico
        first_name (str): Primer nombre del usuario
        last_name (str): Apellido del usuario
        role (RoleSerializer): Objeto serializado del rol del usuario (solo lectura)

    Nota:
        El campo 'role' es de solo lectura y se serializa usando RoleSerializer.
        La contraseña nunca se incluye en las respuestas.
    """
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]

class CreateUserSerializer(serializers.ModelSerializer):
    """
    Serializador para creación de nuevos usuarios.

    Se utiliza en el endpoint POST /users/create_user/

    Campos de entrada:
        username (str): Nombre único de usuario
        email (str): Dirección de correo electrónico
        password (str): Contraseña del usuario (será hash-ificada)
        first_name (str, opcional): Primer nombre
        last_name (str, opcional): Apellido
        role (int): ID del rol a asignar al usuario

    Campos de salida:
        id (int): ID del usuario creado
        username (str): Nombre de usuario
        email (str): Correo del usuario
        first_name (str): Primer nombre
        last_name (str): Apellido
        role (int): ID del rol

    Validaciones:
        - password: Se valida contra las reglas de contraseña de Django
        - username: Debe ser único
        - email: Debe ser un correo válido
        - role: Debe existir en la base de datos

    Nota:
        - La contraseña no se retorna en la respuesta
        - Si el rol es 'student' o 'instructor', se crea automáticamente el perfil correspondiente
    """
    password = serializers.CharField(write_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "password"]

    def validate_password(self, value):
        """Valida que la contraseña cumpla con los estándares de Django."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """
        Crea un nuevo usuario con la contraseña hash-ificada.

        Proceso:
            1. Extrae la contraseña de los datos validados
            2. Crea la instancia de User con los datos restantes
            3. Hash-ifica la contraseña usando set_password()
            4. Guarda el usuario en la base de datos
            5. Un signal en accounts/signals.py crea automáticamente el perfil Student/Instructor

        Args:
            validated_data: Datos validados del serializador

        Returns:
            User: Instancia del usuario creado
        """
        password = validated_data.pop("password")
        u = User(**validated_data)
        u.set_password(password)
        u.save()
        return u


class AdminStatisticsSerializer(serializers.Serializer):
    """
    Serializador para estadísticas administrativas del sistema.

    Se utiliza en el endpoint GET /users/statistics/

    Retorna un diccionario con estadísticas completas del sistema académico
    que incluye información sobre usuarios, materias, inscripciones y desempeño.

    Campos:
        users (dict): Información sobre usuarios por rol y estado
            Incluye:
                - total_students: Total de estudiantes
                - total_instructors: Total de instructores
                - total_admins: Total de administradores
                - active_students: Estudiantes con al menos una inscripción
                - inactive_students: Estudiantes sin inscripciones

        subjects (dict): Información sobre materias
            Incluye:
                - total_subjects: Total de materias
                - subjects_with_instructor: Materias con profesor asignado
                - subjects_without_instructor: Materias sin profesor asignado
                - avg_subjects_per_instructor: Promedio de materias por profesor

        enrollments (dict): Estado de todas las inscripciones
            Incluye:
                - total_enrollments: Total de inscripciones
                - enrollments_enrolled: Inscripciones activas
                - enrollments_approved: Inscripciones aprobadas
                - enrollments_failed: Inscripciones reprobadas
                - enrollments_closed: Inscripciones cerradas

        academic_performance (dict): Métricas de desempeño académico
            Incluye:
                - approval_rate: Porcentaje de aprobación
                - failure_rate: Porcentaje de reprobación
                - system_average_grade: Promedio de calificaciones del sistema
                - average_student_gpa: Promedio de GPA de estudiantes

        grade_distribution (dict): Distribución de calificaciones por rangos
            Incluye:
                - 0_1: Calificaciones en rango [0.0, 1.0)
                - 1_2: Calificaciones en rango [1.0, 2.0)
                - 2_3: Calificaciones en rango [2.0, 3.0)
                - 3_4: Calificaciones en rango [3.0, 4.0)
                - 4_5: Calificaciones en rango [4.0, 5.0]

        professors_with_assignments (int): Total de profesores con materias asignadas

    Nota:
        Este serializador es de solo lectura y se utiliza únicamente para
        serializar datos de salida, no para recibir datos de entrada.
    """

    users = serializers.DictField(
        help_text="Información sobre usuarios (total de estudiantes, profesores, admins, activos e inactivos)"
    )
    subjects = serializers.DictField(
        help_text="Información sobre materias (total, con profesor, sin profesor, promedio por profesor)"
    )
    enrollments = serializers.DictField(
        help_text="Información sobre inscripciones (total, por estado)"
    )
    academic_performance = serializers.DictField(
        help_text="Desempeño académico (tasa de aprobación, promedio del sistema, GPA promedio)"
    )
    grade_distribution = serializers.DictField(
        help_text="Distribución de calificaciones por rango"
    )
    professors_with_assignments = serializers.IntegerField(
        help_text="Total de profesores con materias asignadas"
    )
