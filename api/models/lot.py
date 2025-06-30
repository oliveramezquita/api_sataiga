from django.db import models


class Lot(models.Model):
    _id = models.CharField(max_length=50)
    home_production_id = models.CharField(max_length=50)
    prototype = models.CharField(max_length=50)
    block = models.CharField(max_length=25)
    lot = models.CharField(max_length=25)
    laid = models.CharField(max_length=10)
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True)
    progress = models.JSONField(null=True)
