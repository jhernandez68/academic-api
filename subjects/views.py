from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsAdmin, IsInstructor, IsStudent
from common.decorators import validate_prerequisites
from .models import Subject, Enrollment
from .serializers import SubjectSerializer, EnrollmentSerializer
from . import services
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().order_by("id")
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    def get_permissions(self):
        if self.action in ["create","update","partial_update","destroy","assign_instructor"]:
            return [IsAdmin()]
        return [IsAuthenticated()]
    @action(detail=True, methods=["post"])
    def assign_instructor(self, request, pk=None):
        s = services.assign_instructor(pk, request.data.get("instructor_user_id"))
        return Response(SubjectSerializer(s).data)
class StudentViewSet(viewsets.GenericViewSet):
    serializer_class = EnrollmentSerializer
    queryset = Enrollment.objects.all()
    permission_classes = [IsAuthenticated, IsStudent]
    @action(detail=False, methods=["post"])
    @validate_prerequisites
    def enroll(self, request):
        e = services.enroll(request.user, request.data.get("subject_id"))
        return Response({"id": e.id}, status=status.HTTP_201_CREATED)
    @action(detail=False, methods=["get"])
    def enrolled(self, request):
        qs = services.enrolled_subjects(request.user)
        return Response(EnrollmentSerializer(qs, many=True).data)
    @action(detail=False, methods=["get"])
    def approved(self, request):
        qs = services.approved_subjects(request.user)
        return Response(EnrollmentSerializer(qs, many=True).data)
    @action(detail=False, methods=["get"])
    def failed(self, request):
        qs = services.failed_subjects(request.user)
        return Response(EnrollmentSerializer(qs, many=True).data)
    @action(detail=False, methods=["get"])
    def gpa(self, request):
        v = services.gpa(request.user)
        return Response({"gpa": float(v)})
    @action(detail=False, methods=["get"])
    def history(self, request):
        qs = services.history(request.user)
        return Response(EnrollmentSerializer(qs, many=True).data)
class InstructorViewSet(viewsets.GenericViewSet):
    serializer_class = EnrollmentSerializer
    queryset = Enrollment.objects.all()
    permission_classes = [IsAuthenticated, IsInstructor]
    @action(detail=False, methods=["get"])
    def assigned_subjects(self, request):
        qs = Subject.objects.filter(assigned_instructor=request.user)
        return Response(SubjectSerializer(qs, many=True).data)
    @action(detail=False, methods=["get"])
    def students(self, request):
        subject_id = request.query_params.get("subject_id")
        qs = services.students_by_subject(request.user, subject_id)
        return Response(EnrollmentSerializer(qs, many=True).data)
    @action(detail=False, methods=["post"])
    def grade(self, request):
        enrollment_id = request.data.get("enrollment_id")
        value = float(request.data.get("value"))
        e = services.grade(request.user, enrollment_id, value)
        return Response(EnrollmentSerializer(e).data)
    @action(detail=False, methods=["post"])
    def close(self, request):
        subject_id = request.data.get("subject_id")
        ok = services.close_subject(request.user, subject_id)
        return Response({"closed": ok})
