from django.db import models


class InventoryQuantity(models.Model):
    _id = models.CharField(max_length=50)
    inventory_id = models.CharField(max_length=50)
    inbound_id = models.CharField(max_length=50)
    material_id = models.CharField(max_length=50)
    project = models.JSONField()
    quantity = models.FloatField(default=0)
    rack = models.CharField(max_length=25, null=True)
    level = models.CharField(max_length=25, null=True)
    module = models.CharField(max_length=25, null=True)
    created_at = models.DateTimeField(null=True)
