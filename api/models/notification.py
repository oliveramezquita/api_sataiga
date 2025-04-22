from django.db import models


class Notification(models.Model):
    _id = models.CharField(max_length=50)
    icon = models.CharField(max_length=25)
    title = models.CharField(max_length=50)
    subtitle = models.TextField()
    is_seen = models.BooleanField(default=False)
    user_id = models.CharField(max_length=50, null=True)
    roles = models.JSONField(null=True)
