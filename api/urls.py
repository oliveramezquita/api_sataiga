from django.urls import path
from api.views import *

urlpatterns = [
    path('sections', SectionView.as_view(), name="sections"),
    path('tree-view-sections', TreeView.as_view(), name="treee_view_sections"),
    path('section/<str:id>', SectionViewById.as_view(), name="section"),
    path('roles', RoleView.as_view(), name="roles"),
    path('role/<str:id>', RoleByIdView.as_view(), name="role"),
    path('update-permissions/<str:id>',
         UpdatePermissionsView.as_view(), name="update_permissions"),
    path('users', UserView.as_view(), name='users'),
    path('user/<str:id>', UserByIdView.as_view(), name='user'),
    path('register/<str:id>', RegisterView.as_view(), name='register'),
    path('change-password/<str:id>',
         UpdatePasswordView.as_view(), name='update_password'),
    path('login', AuthView.as_view(), name='login'),
    path('password-request', PasswordRequestView.as_view(), name="password_request"),
    path('restore-password', RestorePasswordView.as_view(), name="restore_password"),
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('clients', ClientView.as_view(), name='clients'),
    path('clients/<str:client_type>',
         ClientByTypeView.as_view(), name="client by type"),
    path('client/<str:id>', ClientByIdView.as_view(), name="client"),
    path('suppliers', SupplierView.as_view(), name='suppliers'),
    path('supplier/<str:id>', SupplierByIdView.as_view(), name='supplier'),
    path('prototypes', PrototypeView.as_view(), name='prototypes'),
    path('prototype/<str:id>', PrototypeByIdView.as_view(), name='prototype'),
    path('prototype_by_client/<str:client_id>',
         PrototypeByClientView.as_view(), name='prototype by client'),
    path('catalogs', CatalogView.as_view(), name="catalogs"),
    path('catalog/<str:id>', CatalogByIdView.as_view(), name='catalog'),
    path('materials', MatrialView.as_view(), name='materials'),
    path('material/<str:id>', MaterialByIdView.as_view(), name='material'),
    path('volumetries', VolumetryView.as_view(), name='volumetries'),
    path('volumetry/<str:id>', VolumetryByIdView.as_view(), name='volumetry'),
    path('upload_volumetry', VolumetryUploadView.as_view(), name="upload volumetry"),
]
