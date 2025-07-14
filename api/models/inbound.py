from django.db import models


class Inbound(models.Model):
    _id = models.CharField(max_length=50)
    purchase_order_id = models.CharField(max_length=50)
    project = models.JSONField()
    items = models.JSONField()
    created_at = models.DateTimeField(null=True)
