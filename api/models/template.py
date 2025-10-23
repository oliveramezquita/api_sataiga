from django.db import models


class Template(models.Model):
    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50, null=True)
    name = models.CharField(max_length=100)
    materials = models.JSONField(null=True)
    equipment = models.JSONField(null=True)
    production = models.JSONField(null=True)
    indirect = models.SmallIntegerField(null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    iva = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
