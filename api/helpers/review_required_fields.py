import logging
from typing import Any, Dict
from rest_framework.exceptions import ValidationError


logger = logging.getLogger(__name__)


def review_required_fields(required_fields: Dict[str, Any], data: Dict[str, Any]):
    if not isinstance(required_fields, dict):
        logger.error("Los campos obligatorios deben ser un diccionario.")
        raise ValidationError(
            "Los campos obligatorios deben ser un diccionario.")
    if not isinstance(data, dict):
        logger.error("El payload debe ser un diccionario.")
        raise ValidationError("El payload debe ser un diccionario.")

    for field, expected_type in required_fields.items():
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            logger.error(f"El valor {field} es requerido.")
            raise ValidationError(f"El valor {field} es requerido.")
        if not isinstance(value, expected_type):
            logger.error(f"El valor {field} debe ser de tipo {expected_type}.")
            raise ValidationError(
                f"El valor {field} debe ser de tipo {expected_type}.")
