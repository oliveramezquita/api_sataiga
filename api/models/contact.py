from django.db import models


class Contact(models.Model):
    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, null=True)
    email = models.EmailField(max_length=254, null=True)
