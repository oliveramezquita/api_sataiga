from django.db import models


class Inventory(models.Model):
    _id = models.CharField(max_length=50)
    material = models.JSONField()
    quantity = models.FloatField(default=0)
    last_inbound = models.JSONField(null=True)
    last_output = models.JSONField(null=True)
    availability = models.JSONField(null=True)
