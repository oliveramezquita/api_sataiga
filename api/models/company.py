from django.db import models


class Company(models.Model):
    _id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    rfc = models.CharField(max_length=15)
    address = models.CharField(max_length=255, null=True)
    postal_code = models.CharField(max_length=5, null=True)
    city = models.CharField(max_length=50, null=True)
    state = models.CharField(max_length=50, null=True)
    email = models.CharField(max_length=255, null=True)
