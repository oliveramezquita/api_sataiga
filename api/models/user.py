from django.db import models


class User(models.Model):
    _id = models.CharField(max_length=50)
    role_id = models.CharField(max_length=50)
    role = models.JSONField(null=True)
    name = models.CharField(max_length=50)
    lastname = models.CharField(max_length=100, null=True)
    email = models.EmailField()
    status = models.PositiveSmallIntegerField()
    avatar = models.TextField(null=True)
    permissions = models.JSONField(null=True)
