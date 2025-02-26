import logging
import traceback
from api.helpers.http_responses import error

log = logging.getLogger(__name__)


class ExceptionHandling:
    @staticmethod
    def exception_handler(method):
        def wrapper(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except Exception as e:
                log.error("Detalles del traceback:\n%s",
                          traceback.format_exc())
                return error(f"Ocurrió una excepción en {method.__name__}: {e}")
        return wrapper
