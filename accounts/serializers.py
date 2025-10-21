from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Student, Instructor, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "display_name"]

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]

class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "password"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        u = User(**validated_data)
        u.set_password(password)
        u.save()
        if u.role and u.role.name == "student":
            Student.objects.create(user=u)
        if u.role and u.role.name == "instructor":
            Instructor.objects.create(user=u)
        return u


class AdminStatisticsSerializer(serializers.Serializer):
    """Serializer para las estadísticas generales del sistema"""

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
