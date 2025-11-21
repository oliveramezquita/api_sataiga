import functools
import logging
from api.helpers.http_responses import ok, created, bad_request, not_found

logger = logging.getLogger(__name__)


def service_method(success_status: str = "ok"):
    """
    Decorador para estandarizar manejo de errores, logging y respuesta.
    - success_status puede ser: "ok" o "created".
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                # Si la función devuelve explícitamente una respuesta (dict, string, etc.), la usamos.
                if isinstance(result, (dict, list, str, int, float, type(None))):
                    if success_status == "created":
                        return created(result)
                    return ok(result)

                # Si el método ya devolvió una respuesta HTTP, la respetamos.
                return result

            except ValueError as e:
                logger.warning(f"[ValueError] {func.__name__}: {e}")
                return bad_request(str(e))

            except LookupError as e:
                logger.warning(f"[LookupError] {func.__name__}: {e}")
                return not_found(str(e))

            except Exception as e:
                logger.exception(f"[UnexpectedError] {func.__name__}: {e}")
                return bad_request(f"Error inesperado en {func.__name__}: {e}")
        return wrapper
    return decorator
