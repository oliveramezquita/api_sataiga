from django.db import models


class Customer(models.Model):
    _id = models.CharField(max_length=50)
    project = models.JSONField()
    warranty = models.JSONField()
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone = models.CharField(max_length=20)
    status = models.SmallIntegerField(default=0)
