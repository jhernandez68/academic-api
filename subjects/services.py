from decimal import Decimal
from django.db.models import Avg
from .models import Subject, Enrollment
def can_enroll(user, subject_id):
    if user.role != "student":
        return False, "not authorized"
    s = Subject.objects.get(id=subject_id)
    if Enrollment.objects.filter(student=user, subject=s, state__in=["approved","enrolled","closed"]).exists():
        return False, "already taken or enrolled"
    reqs = s.prerequisites.all()
    approved = set(Enrollment.objects.filter(student=user, state="approved").values_list("subject_id", flat=True))
    for r in reqs:
        if r.id not in approved:
            return False, "missing prerequisites"
    max_credits = user.student.max_credits_per_term if hasattr(user, "student") else 0
    current = Enrollment.objects.filter(student=user, state="enrolled").select_related("subject")
    used = sum([e.subject.credits for e in current])
    if used + s.credits > max_credits:
        return False, "credits exceeded"
    return True, "ok"
def enroll(user, subject_id):
    s = Subject.objects.get(id=subject_id)
    e, _ = Enrollment.objects.get_or_create(student=user, subject=s, defaults={"state":"enrolled"})
    return e
def enrolled_subjects(user):
    return Enrollment.objects.filter(student=user, state="enrolled").select_related("subject")
def approved_subjects(user):
    return Enrollment.objects.filter(student=user, state="approved").select_related("subject")
def failed_subjects(user):
    return Enrollment.objects.filter(student=user, state="failed").select_related("subject")
def gpa(user):
    qs = Enrollment.objects.filter(student=user).exclude(grade__isnull=True)
    if not qs.exists():
        return Decimal("0.0")
    return qs.aggregate(a=Avg("grade"))["a"] or Decimal("0.0")
def history(user):
    return Enrollment.objects.filter(student=user).select_related("subject").order_by("created_at")
def students_by_subject(instructor, subject_id):
    return Enrollment.objects.filter(subject_id=subject_id, subject__assigned_instructor=instructor)
def grade(instructor, enrollment_id, value):
    if value < 0 or value > 5:
        raise ValueError("invalid range")
    e = Enrollment.objects.select_related("subject").get(id=enrollment_id, subject__assigned_instructor=instructor)
    e.grade = round(Decimal(value),1)
    e.state = "approved" if e.grade >= 3 else "failed"
    e.save()
    from notifications.models import Notification
    Notification.objects.create(user=e.student, type="grade", message=f"Grade {e.grade} in {e.subject.name}")
    return e
def close_subject(instructor, subject_id):
    qs = Enrollment.objects.filter(subject_id=subject_id, subject__assigned_instructor=instructor)
    if not qs.exists():
        return False
    if qs.filter(grade__isnull=True).exists():
        return False
    qs.update(state="closed")
    return True
def assign_instructor(subject_id, instructor_user_id):
    from accounts.models import User
    s = Subject.objects.get(id=subject_id)
    p = User.objects.get(id=instructor_user_id, role="instructor")
    s.assigned_instructor = p
    s.save()
    return s
