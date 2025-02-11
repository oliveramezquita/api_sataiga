from django.urls import path
from api.views import *

urlpatterns = [
    path('roles', RolesView.as_view(), name="roles"),
    path('role/<int:id>', RoleByIdView.as_view(), name="rol"),
    path('users', UsersView.as_view(), name='users'),
    path('user/<int:id>', UserByIdView.as_view(), name='user'),
    path('login', AuthView.as_view(), name='login'),
    path('change_password/<int:id>',
         UpdatePasswordView.as_view(), name='update_password'),
    path('password_request', PasswordRequestView.as_view(), name="password_request"),
    path('restore_password', RestorePasswordView.as_view(), name="restore_password"),
]
