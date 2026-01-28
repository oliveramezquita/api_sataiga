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


class SafeTrendField(serializers.Field):
    """
    Para dicts (Mongo) y modelos Django.
    Si la key/atributo no existe -> regresa default sin lanzar KeyError.
    """

    def __init__(self, default_object=None, **kwargs):
        self.default_object = default_object or {"type": None, "value": None}
        # allow_null ayuda en representaciones
        kwargs.setdefault("allow_null", True)
        # required=False evita que en input lo exija
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        """
        Evita KeyError cuando instance es dict y no tiene la key.
        """
        # Si es dict (caso Mongo)
        if isinstance(instance, dict):
            return instance.get(self.field_name, self.default_object)

        # Si es modelo Django u objeto normal
        return getattr(instance, self.field_name, self.default_object)

    def to_representation(self, value):
        if value in (None, "", {}):
            return self.default_object

        if not isinstance(value, dict):
            return self.default_object

        return {
            "type": value.get("type"),
            "value": value.get("value"),
        }

    def to_internal_value(self, data):
        # Para POST/PUT/PATCH
        if data in (None, "", {}):
            return self.default_object

        if not isinstance(data, dict):
            raise serializers.ValidationError("trend debe ser un objeto.")

        return {
            "type": data.get("type"),
            "value": data.get("value"),
        }
