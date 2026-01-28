from django.db import models


class Trend(models.Model):
    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50)
    front = models.CharField(max_length=100)
    melamines = models.JSONField(null=True)
    granites = models.JSONField(null=True)
