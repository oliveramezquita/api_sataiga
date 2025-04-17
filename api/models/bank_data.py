from django.db import models


class BankData(models.Model):
    _id = models.CharField(max_length=50)
    supplier_id = models.CharField(max_length=50)
    bank = models.CharField(max_length=50)
    account_number = models.CharField(max_length=34, null=True)
    card_number = models.CharField(max_length=16, null=True)
    clabe = models.CharField(max_length=18, null=True)
    holder = models.CharField(max_length=100, null=True)
    credit_term = models.CharField(max_length=25, null=True)
