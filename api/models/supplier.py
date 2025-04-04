from django.db import models


class Supplier(models.Model):
    _id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=20, null=True)
    email = models.EmailField(max_length=254, null=True)
    contact = models.CharField(max_length=100, null=True)
