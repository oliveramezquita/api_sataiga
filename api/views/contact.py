from rest_framework import views
from api.use_cases.contact_use_case import ContactUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class ContactsView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request, client_id):
        use_case = ContactUseCase(client_id=client_id, data=request.data)
        return use_case.save()

    def get(self, request, client_id):
        use_case = ContactUseCase(client_id=client_id)
        return use_case.get()


class ContactByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = ContactUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = ContactUseCase(id=id)
        return use_case.delete()
