from django.db import models


class Warranty(models.Model):
    _id = models.CharField(
        max_length=50,
        primary_key=True
    )
    name = models.CharField(max_length=50)

    duration = models.DecimalField(
        max_digits=4,
        decimal_places=2
    )

    is_available = models.BooleanField(default=True)
