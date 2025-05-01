from django.db import models


class Explosion(models.Model):
    _id = models.CharField(max_length=50)
    home_production_id = models.CharField(max_length=50)
    material_id = models.CharField(max_length=50)
    explosion = models.JSONField(null=True)
    gran_total = models.FloatField(default=0)
