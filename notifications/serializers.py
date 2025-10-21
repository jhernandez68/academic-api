from rest_framework import serializers
from .models import Notification
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id","user","type","message","created","read"]
        read_only_fields = ["user","created"]
