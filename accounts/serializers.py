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
