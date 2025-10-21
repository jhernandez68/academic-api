import csv
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from accounts.models import User, Role
from subjects.models import Enrollment

class StudentReportCSV(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        student_role = Role.objects.get(name="student")
        u = User.objects.get(id=id, role=student_role)
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="student_report_{u.id}.csv"'
        w = csv.writer(resp)
        w.writerow(["Name","Subject","Grade","State"])
        ins = Enrollment.objects.filter(student=u).select_related("subject")
        for i in ins:
            w.writerow([u.get_full_name() or u.username, i.subject.name, i.grade, i.state])
        return resp
class InstructorReportCSV(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        instructor_role = Role.objects.get(name="instructor")
        u = User.objects.get(id=id, role=instructor_role)
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="instructor_report_{u.id}.csv"'
        w = csv.writer(resp)
        w.writerow(["Name","Subject","Average"])
        subjects = u.subject_set.all() if hasattr(u, "subject_set") else []
        for s in subjects:
            ins = Enrollment.objects.filter(subject=s).exclude(grade__isnull=True)
            avg = None
            if ins.exists():
                avg = sum([float(x.grade) for x in ins]) / ins.count()
            w.writerow([u.get_full_name() or u.username, s.name, avg])
        return resp
