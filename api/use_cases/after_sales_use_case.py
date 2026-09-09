from api.helpers.get_query_params import get_query_params
from api.decorators.service_method import service_method
from api.services.auth_service import AuthService


class AfterSalesUseCase:
    def __init__(self, request=None, **kwargs):
        self.params = get_query_params(request)
        self.auth_service = AuthService()

    @service_method()
    def send_invitation(self):
        name = self.params.get('name')
        email = self.params.get('email')

        self.auth_service.send_invitation(name, email)
        return "La invitación ha sido enviada con éxito."
