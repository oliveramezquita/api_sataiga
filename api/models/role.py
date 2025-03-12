from django.db import models


class Role(models.Model):
    _id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=20)
    permissions = models.JSONField(null=True)
    status = models.PositiveSmallIntegerField()
