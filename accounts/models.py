from django.db import models
from django.contrib.auth.models import AbstractUser
class User(AbstractUser):
    ROLE_CHOICES = [("admin","admin"),("instructor","instructor"),("student","student")]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student")
    max_credits_per_term = models.PositiveIntegerField(default=16)
class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="instructor")
    max_credits_per_term = models.PositiveIntegerField(default=20)
