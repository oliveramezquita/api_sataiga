from django.db import models


class Prototype(models.Model):
    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50)
    client_name = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    front = models.CharField(max_length=100)
    tendencies = models.JSONField(null=True)
