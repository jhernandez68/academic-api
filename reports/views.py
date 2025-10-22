import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from common.permissions import IsAdmin, IsInstructor
from accounts.models import User, Role
from subjects.models import Subject, Enrollment

class StudentReportCSV(APIView):
    """
    Genera un reporte CSV con las materias inscritas de un estudiante,
    sus calificaciones y estado de aprobación.

    Solo administradores pueden descargar reportes de cualquier estudiante.
    Los estudiantes solo pueden descargar su propio reporte.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        student_role = Role.objects.get(name="student")
        u = User.objects.get(id=id, role=student_role)

        # Validación de permisos: admin o el mismo estudiante
        if not (request.user.role and request.user.role.name == "admin") and request.user.id != id:
            return Response(
                {"error": "No tienes permiso para acceder a este reporte"},
                status=status.HTTP_403_FORBIDDEN
            )

        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="student_report_{u.id}.csv"'
        w = csv.writer(resp)
        w.writerow(["Name","Subject","Grade","State"])
        ins = Enrollment.objects.filter(student=u).select_related("subject")
        for i in ins:
            w.writerow([u.get_full_name() or u.username, i.subject.name, i.grade, i.state])
        return resp

class InstructorReportCSV(APIView):
    """
    Genera un reporte CSV con las materias impartidas por un instructor,
    y el promedio de calificaciones de cada materia.

    Solo administradores pueden descargar reportes de cualquier instructor.
    Los instructores solo pueden descargar su propio reporte.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        instructor_role = Role.objects.get(name="instructor")
        u = User.objects.get(id=id, role=instructor_role)

        # Validación de permisos: admin o el mismo instructor
        if not (request.user.role and request.user.role.name == "admin") and request.user.id != id:
            return Response(
                {"error": "No tienes permiso para acceder a este reporte"},
                status=status.HTTP_403_FORBIDDEN
            )

        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="instructor_report_{u.id}.csv"'
        w = csv.writer(resp)
        w.writerow(["Name","Subject","Average"])

        # Usar assigned_subjects que es el related_name correcto
        subjects = Subject.objects.filter(assigned_instructor=u)
        for s in subjects:
            ins = Enrollment.objects.filter(subject=s).exclude(grade__isnull=True)
            avg = None
            if ins.exists():
                avg = sum([float(x.grade) for x in ins]) / ins.count()
            w.writerow([u.get_full_name() or u.username, s.name, avg])
        return resp
