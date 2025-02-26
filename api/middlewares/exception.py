import logging
import traceback
from django.http import JsonResponse

log = logging.getLogger(__name__)


class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        log.error("Ocurrió una excepción: %s", exception)
        log.error("Detalles del traceback:\n%s", traceback.format_exc())

        response_data = {
            'error': 'Ocurrió un error al momento de procesar la petición.',
            'details': str(exception)
        }
        return JsonResponse(response_data, status=500)
