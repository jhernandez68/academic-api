from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Student, Instructor
from notifications.models import Notification

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created and instance.role:
        if instance.role.name == "student":
            Student.objects.create(user=instance)
        if instance.role.name == "instructor":
            Instructor.objects.create(user=instance)
        Notification.objects.create(user=instance, type="welcome", message="User created")
