from django.db import models


class Volumetry(models.Model):
    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50)
    front = models.CharField(max_length=100)
    material_id = models.CharField(max_length=50)
    volumetry = models.JSONField(null=True)
