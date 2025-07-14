from django.db import models


class Inventory(models.Model):
    _id = models.CharField(max_length=50)
    rack = models.CharField(max_length=25, null=True)
    level = models.CharField(max_length=25, null=True)
    module = models.CharField(max_length=25, null=True)
    material = models.JSONField()
    quantity = models.FloatField(default=0)
