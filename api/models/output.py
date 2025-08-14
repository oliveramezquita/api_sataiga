from django.db import models


class Output(models.Model):
    STATUS_REQUESTED = 0
    STATUS_APPROVED = 1
    STATUS_REFUND_REQUESTED = 2
    STATUS_PARTIALLY_RETURNED = 3
    STATUS_FULLY_RETURNED = 4
    STATUS_CACELLED = 5

    STATUS_CHOICES = [
        (STATUS_REQUESTED, 'Solicitada'),
        (STATUS_APPROVED, 'Aprobada'),
        (STATUS_REFUND_REQUESTED, 'Devolución solicitada'),
        (STATUS_PARTIALLY_RETURNED, 'Devolución parcial'),
        (STATUS_FULLY_RETURNED, 'Devolución total'),
        (STATUS_CACELLED, 'Cancelada'),
    ]

    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50, null=True)
    quantification = models.JSONField()
    items = models.JSONField()
    selected_items = models.JSONField(null=True)
    created_at = models.DateTimeField(null=True)
    updated_at = models.DateTimeField(null=True)
    folio = models.IntegerField()
    status = models.IntegerField(
        choices=STATUS_CHOICES, default=STATUS_REQUESTED)
