from django.db import models


class RefreshRate(models.Model):
    _id = models.CharField(max_length=50)
    supplier_id = models.CharField(max_length=50)
    value = models.CharField(max_length=25)
    next_date = models.DateTimeField(null=True)
    history = models.JSONField(null=True)
