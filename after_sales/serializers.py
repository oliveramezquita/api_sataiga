"""Serializers de entrada para los endpoints de autenticación."""
from rest_framework import serializers

from after_sales.constants import PURPOSE_TO_VERIFICATION_TYPE


class IdentifySerializer(serializers.Serializer):
    identifier = serializers.CharField()


class _DeviceMixin(serializers.Serializer):
    device_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    device_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    device_type = serializers.ChoiceField(
        choices=["ios", "android", "web"], required=False, allow_null=True
    )


class VerificationSendSerializer(_DeviceMixin):
    identifier = serializers.CharField()
    purpose = serializers.ChoiceField(choices=list(PURPOSE_TO_VERIFICATION_TYPE))


class VerificationConfirmSerializer(_DeviceMixin):
    identifier = serializers.CharField()
    code = serializers.CharField()
    purpose = serializers.ChoiceField(choices=list(PURPOSE_TO_VERIFICATION_TYPE))


class ActivateSerializer(_DeviceMixin):
    activation_token = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField(required=False, allow_null=True)
    biometric_enabled = serializers.BooleanField(required=False, default=False)


class LoginSerializer(_DeviceMixin):
    identifier = serializers.CharField()
    password = serializers.CharField()


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    code = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField(required=False, allow_null=True)
