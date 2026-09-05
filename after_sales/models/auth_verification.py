from django.db import models


class AuthVerification(models.Model):
    _id = models.CharField(
        max_length=50,
        primary_key=True
    )

    auth_id = models.CharField(
        max_length=50
    )

    device_id = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    verification_type = models.CharField(
        max_length=30,
        choices=[
            ("activation", "Activation"),
            ("login", "Login"),
            ("password_reset", "Password Reset"),
            ("phone_change", "Phone Change"),
            ("email_change", "Email Change"),
        ]
    )

    verification_method = models.CharField(
        max_length=20,
        choices=[
            ("sms", "SMS"),
            ("email", "Email"),
        ]
    )

    # IMPORTANTE:
    # Idealmente almacenar el hash del código,
    # no el código en texto plano.
    code = models.CharField(
        max_length=255
    )

    expires_at = models.DateTimeField()

    attempts = models.PositiveSmallIntegerField(
        default=0
    )

    verified = models.BooleanField(
        default=False
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )
