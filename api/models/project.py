from django.db import models


class Project(models.Model):
    STATUS_DISENO = 0
    STATUS_COTIZACION = 1
    STATUS_PRODUCCION = 2
    STATUS_INSTALACION = 3
    STATUS_ENTREGADO = 4

    STATUS_CHOICES = [
        (STATUS_DISENO, 'Diseño'),
        (STATUS_COTIZACION, 'Cotización'),
        (STATUS_PRODUCCION, 'Producción'),
        (STATUS_INSTALACION, 'Instalación'),
        (STATUS_ENTREGADO, 'Entregado'),
    ]

    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    front = models.CharField(max_length=100)
    location = models.CharField(max_length=100, null=True)
    payment_method = models.CharField(max_length=50, null=True)
    payment_form = models.CharField(max_length=50, null=True)
    version = models.CharField(max_length=5)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    iva = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    advance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    liquidation = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=STATUS_DISENO)
