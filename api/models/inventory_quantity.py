from django.db import models


class InventoryQuantity(models.Model):
    STATUS_EN_INVENTARIO = 0
    STATUS_PARCIALMENTE = 1
    STATUS_RETIRADO = 2

    STATUS_CHOICES = [
        (STATUS_EN_INVENTARIO, 'Disponible'),
        (STATUS_PARCIALMENTE, 'Parcialmente retirado'),
        (STATUS_RETIRADO, 'Retirado del almacén'),
    ]

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
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=STATUS_EN_INVENTARIO)
