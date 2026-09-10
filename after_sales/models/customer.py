from django.db import models


class Customer(models.Model):
    _id = models.CharField(
        max_length=50,
        primary_key=True
    )

    project = models.JSONField()

    warranty = models.JSONField()

    name = models.CharField(max_length=150)

    address = models.CharField(max_length=255)

    is_deleted = models.BooleanField(default=False)

    deleted_at = models.DateTimeField(null=True)
