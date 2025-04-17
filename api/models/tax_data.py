from django.db import models


class TaxData(models.Model):
    _id = models.CharField(max_length=50)
    supplier_id = models.CharField(max_length=50)
    rfc = models.CharField(max_length=15)
    name = models.CharField(max_length=100)
    regime = models.CharField(max_length=50, null=True)
    postal_code = models.CharField(max_length=5, null=True)
    address = models.CharField(max_length=150, null=True)
    constancy = models.CharField(max_length=255, null=True)
