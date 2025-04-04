from django.db import models


class Client(models.Model):
    TYPES = [
        ('VS', 'Vivienda en Serie'),
        ('PE', 'Proyectos ESpeciales'),
    ]

    _id = models.CharField(max_length=50)
    pe_id = models.PositiveSmallIntegerField(null=True)
    type = models.CharField(
        max_length=2,
        choices=TYPES,
        default='VS',
    )
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=255, null=True)
    email = models.EmailField(max_length=254, null=True)
    phone = models.CharField(max_length=20, null=True)
