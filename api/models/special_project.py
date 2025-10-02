from django.db import models


class SpecialProject(models.Model):
    STATUS_DESIGN = 0
    STATUS_PRICE = 1
    STATUS_PRODUCTION = 2
    STATUS_FACILITY = 3

    STATUS_CHOICES = [
        (STATUS_DESIGN, 'Diseño'),
        (STATUS_PRICE, 'Cotización'),
        (STATUS_PRODUCTION, 'Producción'),
        (STATUS_FACILITY, 'Instalación'),
    ]

    _id = models.CharField(max_length=50)
    folio = models.IntegerField()
    client_id = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    version = models.CharField(max_length=25)
    front = models.CharField(max_length=100, null=True)
    location = models.CharField(max_length=100, null=True)
    payment_method = models.CharField(max_length=100, null=True)
    method_payment = models.CharField(max_length=100, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    iva = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    advance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    liquidation = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=STATUS_DESIGN)
