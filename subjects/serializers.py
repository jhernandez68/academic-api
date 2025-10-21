from rest_framework import serializers
from .models import Subject, Enrollment
class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id","name","code","credits","assigned_instructor","prerequisites"]
class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["id","student","subject","state","grade","created_at"]
        read_only_fields = ["state","grade","student"]
