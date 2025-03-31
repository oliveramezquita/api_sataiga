from rest_framework import views
from api.use_cases.catalog_use_case import CatalogUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class CatalogView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = CatalogUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = CatalogUseCase()
        return use_case.get()


class CatalogByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def get(self, request, id):
        use_case = CatalogUseCase(id=id)
        return use_case.get_by_id()

    def patch(self, request, id):
        use_case = CatalogUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = CatalogUseCase(id=id)
        return use_case.delete()
