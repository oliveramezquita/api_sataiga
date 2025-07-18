from django.db import models


class HomeProduction(models.Model):
    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50)
    front = models.CharField(max_length=100)
    od = models.CharField(max_length=25)
    lots = models.JSONField(null=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, null=True)
