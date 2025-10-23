from django.db import models


class Concept(models.Model):
    _id = models.CharField(max_length=50)
    project_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    templates = models.JSONField(null=True)
    added_templates = models.JSONField(null=True)
    materials = models.JSONField(null=True)
    production = models.JSONField(null=True)
    installation = models.JSONField(null=True)
    equipment = models.JSONField(null=True)
    prov = models.JSONField(null=True)
    indirect = models.SmallIntegerField(null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    iva = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
