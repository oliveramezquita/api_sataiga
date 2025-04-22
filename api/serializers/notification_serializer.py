from rest_framework import serializers
from api.models import Notification
from api.helpers.time_ago import time_ago
from datetime import datetime


class NotificationSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField(
        "get_time"
    )

    def get_time(self, data):
        dt = datetime.fromtimestamp(data['created_at'].timestamp())
        return time_ago(dt)

    class Meta:
        model = Notification
        fields = '__all__'
