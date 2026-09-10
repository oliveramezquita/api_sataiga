from django.db import models


class Auth(models.Model):
    STATUS_PENDING = 0
    STATUS_ACTIVE = 1
    STATUS_LOCKED = 2
    STATUS_DISABLED = 3

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending activation"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_LOCKED, "Locked"),
        (STATUS_DISABLED, "Disabled"),
    ]

    _id = models.CharField(
        max_length=50,
        primary_key=True
    )

    user_id = models.CharField(
        max_length=50
    )

    user_type = models.CharField(
        max_length=20,
        choices=[
            ("customer", "Customer"),
            ("technician", "Technician"),
        ]
    )

    # Credentials
    email = models.EmailField(
        max_length=255,
        unique=True
    )

    phone = models.CharField(
        max_length=20,
        unique=True
    )

    password = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # Account status
    status = models.SmallIntegerField(
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    # Login security
    failed_login_attempts = models.PositiveSmallIntegerField(
        default=0
    )

    locked_until = models.DateTimeField(
        null=True,
        blank=True
    )

    # Password
    password_changed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Activation
    activated_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Activity
    last_login = models.DateTimeField(
        null=True,
        blank=True
    )

    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )
