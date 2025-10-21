from celery import shared_task
from django.db.models import Avg
from accounts.models import User
from subjects.models import Subject, Enrollment
from notifications.models import Notification
@shared_task
def weekly_instructor_summary():
    instructors = User.objects.filter(role="instructor")
    for i in instructors:
        subjects = Subject.objects.filter(assigned_instructor=i)
        parts = []
        for s in subjects:
            ins = Enrollment.objects.filter(subject=s).exclude(grade__isnull=True)
            avg = ins.aggregate(a=Avg("grade"))["a"]
            parts.append(f"{s.name}: {avg}")
        msg = "; ".join(parts) if parts else "no data"
        Notification.objects.create(user=i, type="weekly_summary", message=msg)
