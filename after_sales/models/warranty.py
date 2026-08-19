from django.db import models


class Warranty(models.Model):
    _id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    duration = models.DecimalField(max_digits=4, decimal_places=2)
    status = models.SmallIntegerField(default=0)
