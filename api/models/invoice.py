from django.db import models


class Invoice(models.Model):
    _id = models.CharField(max_length=50)
    purchase_order_id = models.CharField(max_length=50)
    folio = models.CharField(max_length=10)
    files = models.JSONField(null=True)
    status = models.BooleanField(default=False)
    updated_at = models.DateTimeField(null=True)
