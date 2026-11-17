import functools
import logging

from rest_framework.exceptions import ValidationError

from .errors import AuthError
from .responses import fail

logger = logging.getLogger(__name__)


def _first_message(detail):
    """Extrae un mensaje legible de un ValidationError de DRF."""
    if isinstance(detail, dict):
        for key, value in detail.items():
            msg = _first_message(value)
            if msg:
                return f"{key}: {msg}" if key != "non_field_errors" else msg
    if isinstance(detail, (list, tuple)) and detail:
        return _first_message(detail[0])
    return str(detail)


def endpoint(func):
    """
    Estandariza el manejo de errores de los métodos del use case,
    de forma equivalente a `api.decorators.service_method` pero
    devolviendo el envelope propio de la app móvil.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AuthError as exc:
            return fail(exc.message, code=exc.code, status=exc.status_code)
        except ValidationError as exc:
            return fail(
                _first_message(exc.detail),
                code="invalid_request",
                status=400,
            )
        except Exception as exc:  # noqa: BLE001 - se registra y se degrada
            logger.exception(
                "after_sales.auth: error inesperado en %s: %s",
                func.__name__,
                exc,
            )
            return fail(
                "Ocurrió un error al procesar la solicitud.",
                code="server_error",
                status=500,
            )

    return wrapper
