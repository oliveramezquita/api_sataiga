from django.db import models


class Inbound(models.Model):
    _id = models.CharField(max_length=50)
    purchase_order_id = models.CharField(max_length=50, null=True)
    supplier_id = models.CharField(max_length=50)
    project = models.JSONField(null=True)
    items = models.JSONField()
    created_at = models.DateTimeField(null=True)
    folio = models.IntegerField()
    notes = models.TextField(null=True)
