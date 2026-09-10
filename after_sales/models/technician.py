from django.db import models


class Technician(models.Model):
    _id = models.CharField(
        max_length=50,
        primary_key=True
    )

    name = models.CharField(max_length=150)

    schedule = models.JSONField(null=True)

    blocked_dates = models.JSONField(null=True)

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True)
