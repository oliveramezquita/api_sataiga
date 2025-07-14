from rest_framework import views
from api.use_cases.company_use_case import CompanyUseCase
from api.middlewares import BellartiAuthenticationMiddleware


class CompaniesView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def post(self, request):
        use_case = CompanyUseCase(data=request.data)
        return use_case.save()

    def get(self, request):
        use_case = CompanyUseCase(request=request)
        return use_case.get()


class CompanyByIdView(views.APIView):
    authentication_classes = [BellartiAuthenticationMiddleware]

    def patch(self, request, id):
        use_case = CompanyUseCase(data=request.data, id=id)
        return use_case.update()

    def delete(self, request, id):
        use_case = CompanyUseCase(id=id)
        return use_case.delete()
