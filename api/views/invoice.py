from rest_framework import views
from api.use_cases.invoice_use_case import InvoiceUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class InvoicesView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request):
        use_case = InvoiceUseCase(request=request)
        return use_case.get()

    def post(self, request):
        use_case = InvoiceUseCase(data=request.data)
        return use_case.save()


class InvoiceView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = InvoiceUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = InvoiceUseCase(id=id, data=request.data)
        return use_case.update()

    def put(self, request, id):
        use_case = InvoiceUseCase(id=id, data=request.data)
        return use_case.upload()
