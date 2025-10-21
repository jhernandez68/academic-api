from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created")
