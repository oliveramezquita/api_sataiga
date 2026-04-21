from django.db import models


class Invoice(models.Model):
    STATUS_PENDIENTE = 0
    STATUS_PAGADA = 1
    STATUS_ELIMINADA = 2

    STATUS_CHOICES = [
        (STATUS_PENDIENTE, 'Pendiente'),
        (STATUS_PAGADA, 'Pagada'),
        (STATUS_ELIMINADA, 'Eliminada'),
    ]

    _id = models.CharField(max_length=50)
    purchase_order_id = models.CharField(max_length=50)
    folio = models.CharField(max_length=10)
    files = models.JSONField(null=True)
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=STATUS_PENDIENTE)
    updated_at = models.DateTimeField(null=True)
