from django.db import models


class Output(models.Model):
    _id = models.CharField(max_length=50)
    client_id = models.CharField(max_length=50, null=True)
    quantification = models.JSONField()
    items = models.JSONField()
    created_at = models.DateTimeField(null=True)
    folio = models.IntegerField()
