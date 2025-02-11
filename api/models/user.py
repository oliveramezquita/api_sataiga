from django.db import models
from api.static import USER_STATUS


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    value = models.CharField(max_length=20, unique=True)


class User(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    lastname = models.CharField(max_length=100, null=True)
    email = models.EmailField()
    status = models.PositiveSmallIntegerField(choices=USER_STATUS, default=0)
    password = models.CharField(max_length=128, null=True)
    avatar = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PasswordRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hash_request = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_request'
