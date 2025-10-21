from django.db import models
from accounts.models import User
class Subject(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    credits = models.PositiveIntegerField()
    prerequisites = models.ManyToManyField("self", symmetrical=False, blank=True, related_name="required_by")
    assigned_instructor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_subjects")
class Enrollment(models.Model):
    STATES = [("enrolled","enrolled"),("approved","approved"),("failed","failed"),("closed","closed")]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_enrollments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="enrollments")
    state = models.CharField(max_length=20, choices=STATES, default="enrolled")
    grade = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("student","subject")
