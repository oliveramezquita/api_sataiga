from django.db import models


class Volumetry(models.Model):
    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50)
    material_id = models.CharField(max_length=50)
    supplier_id = models.CharField(max_length=50)
    front = models.CharField(max_length=100)
    prototype = models.CharField(max_length=100)
    volumetry = models.JSONField(null=True)
    tendencies = models.JSONField(null=True)
    total = models.FloatField(default=0)
