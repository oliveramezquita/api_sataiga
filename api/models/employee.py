from django.db import models


class Employee(models.Model):
    _id = models.CharField(max_length=50)
    number = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    activity = models.CharField(max_length=50)
    hourly_wage = models.DecimalField(max_digits=10, decimal_places=2)
    daily_wage = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.BooleanField(default=True)
