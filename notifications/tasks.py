from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Notification
@shared_task
def purge_old_notifications():
    limit = timezone.now() - timedelta(days=90)
    Notification.objects.filter(created__lt=limit, read=True).delete()
