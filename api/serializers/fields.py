from decimal import Decimal, InvalidOperation
from rest_framework import serializers


class SafeDecimalField(serializers.DecimalField):
    def _clean(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            v = value.strip()
            if v == "":
                return None
            # opcional: soportar comas
            if "," in v:
                if "." in v:
                    v = v.replace(",", "")
                else:
                    v = v.replace(",", ".")
            value = v
        return value

    def to_internal_value(self, data):
        data = self._clean(data)
        if data is None:
            return None
        try:
            return super().to_internal_value(data)
        except (InvalidOperation, ValueError, TypeError):
            raise serializers.ValidationError("Valor decimal inválido.")

    def to_representation(self, value):
        value = self._clean(value)
        if value is None:
            return None
        try:
            return super().to_representation(value)
        except (InvalidOperation, ValueError, TypeError):
            # si en BD hay basura (''), no revientes el endpoint
            return None
