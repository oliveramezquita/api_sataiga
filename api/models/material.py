from django.db import models


class Material(models.Model):
    AREAS = [
        ('CONSUMO INTERNO', 'Consumo Interno'),
        ('OPERACIÓN', 'Operación'),
    ]

    _id = models.CharField(max_length=50)
    supplier_id = models.CharField(max_length=50)
    division = models.CharField(max_length=25)
    name = models.CharField(max_length=25)
    espec1 = models.CharField(max_length=25, null=True)
    espec2 = models.CharField(max_length=25, null=True)
    espec3 = models.CharField(max_length=25, null=True)
    espec4 = models.CharField(max_length=25, null=True)
    espec5 = models.CharField(max_length=50, null=True)
    concept = models.CharField(max_length=50, null=True)
    supplier_code = models.CharField(max_length=25, null=True)
    sku = models.CharField(max_length=50, null=True)
    area = models.CharField(
        max_length=25,
        choices=AREAS,
        null=True)
    minimum = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    maximum = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    measurement = models.CharField(max_length=25)
    presentation = models.CharField(max_length=50, null=True)
    reference = models.CharField(max_length=50, null=True)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    inventory_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    market_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    price_difference = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    automation = models.BooleanField(default=False)
    images = models.JSONField(null=True)
    qr = models.CharField(max_length=255, null=True)
