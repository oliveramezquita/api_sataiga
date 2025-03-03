from django.db import models


class Section(models.Model):
    _id = models.CharField(max_length=50)
    parent = models.CharField(max_length=50)
    level_1 = models.CharField(max_length=50, null=True)
    level_2 = models.CharField(max_length=50, null=True)
    value = models.CharField(max_length=20)
