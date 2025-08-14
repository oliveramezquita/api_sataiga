from django.db import models


class Inbound(models.Model):
    STATUS_REGISTERED = 0
    STATUS_STORED = 1
    STATUS_CANCELLED = 2

    STATUS_CHOICES = [
        (STATUS_REGISTERED, 'Registrada'),
        (STATUS_STORED, 'Almacenda'),
        (STATUS_CANCELLED, 'Cancelada'),
    ]

    _id = models.CharField(max_length=50)
    purchase_order_id = models.CharField(max_length=50, null=True)
    supplier_id = models.CharField(max_length=50)
    project = models.JSONField(null=True)
    items = models.JSONField()
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)
    folio = models.IntegerField()
    notes = models.TextField(null=True)
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=STATUS_REGISTERED)
