from api.helpers.get_query_params import get_query_params
from api.decorators.service_method import service_method
from api.services.volumetry_service import VolumetryService
# from api.functions.quantify import quantify


class VolumetryUseCase:
    def __init__(self, request=None, **kwargs):
        self.request = request
        params = get_query_params(request)
        self.client_id = params.get("client_id")
        self.front = params.get('front')
        self.prototype = params.get('prototype')
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.service = VolumetryService()

    @service_method(success_status="created")
    def save(self):
        self.service.load_volumetry({
            'client_id': self.data.get('client_id'),
            'front': self.data.get('front'),
            'prototype': self.data.get('prototype'),
            'volumetry': self.data.get('volumetry')
        })
        # TODO: Añadir el proceso para crear la cuantificación quantify.delay

        return "La volumetría ha sido cargada correctamente."

    @service_method()
    def get(self):
        """
        Devuelve la volumetría dependiendo de los filtos.
        Si no se pasa client_id, devuelve todas las tendencias.
        """
        return self.service.get(self.client_id, self.front, self.prototype)

    @service_method()
    def upload(self):
        # TODO: Añadir el proceso para crear la cuantificación quantify.delay
        return self.service.upload(
            self.client_id,
            self.front,
            self.prototype,
            self.data,
            self.request.FILES['file'])
