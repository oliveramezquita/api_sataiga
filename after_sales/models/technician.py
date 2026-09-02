from django.db import models


class Technician(models.Model):
    _id = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=20)
    schedule = models.JSONField(null=True)
    blocked_dates = models.JSONField(null=True)
    status = models.SmallIntegerField(default=0)
