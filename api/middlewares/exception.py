import logging

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class ExceptionMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):
        logger.exception(
            "Error no controlado | %s %s",
            request.method,
            request.path,
        )

        return JsonResponse(
            {
                "error": (
                    "Ocurrió un error al momento "
                    "de procesar la petición."
                )
            },
            status=500,
        )
