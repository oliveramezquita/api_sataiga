from django.db import models


class AuthDevice(models.Model):
    _id = models.CharField(
        max_length=50,
        primary_key=True
    )

    auth_id = models.CharField(
        max_length=50
    )

    # Identificador generado por la aplicación
    device_id = models.CharField(
        max_length=255
    )

    device_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    device_type = models.CharField(
        max_length=20,
        choices=[
            ("ios", "iOS"),
            ("android", "Android"),
            ("web", "Web"),
        ],
        null=True,
        blank=True
    )

    # Dispositivo confiable
    trusted = models.BooleanField(
        default=False
    )

    # El usuario habilitó biometría
    biometric_enabled = models.BooleanField(
        default=False
    )

    # Información de actividad
    last_login = models.DateTimeField(
        null=True,
        blank=True
    )

    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    # Fecha en que se verificó/autorizó el dispositivo
    verified_at = models.DateTimeField(
        null=True,
        blank=True
    )
