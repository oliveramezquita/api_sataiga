from django.db import models


class Quantification(models.Model):
    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50)
    front = models.CharField(max_length=100)
    prototype = models.CharField(max_length=50)
    quantification = models.JSONField()
