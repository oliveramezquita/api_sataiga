from django.db import models


class Catalog(models.Model):
    _id = models.CharField(max_length=50)
    name = models.CharField(max_length=25)
    values = models.JSONField()
