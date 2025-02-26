from django.urls import path
from api.views import *

urlpatterns = [
    path('roles', RoleView.as_view(), name="roles"),
    path('role/<str:id>', RoleByIdView.as_view(), name="role"),
    path('users', UserView.as_view(), name='users'),
    path('user/<str:id>', UserByIdView.as_view(), name='user'),
    path('register/<str:id>', RegisterView.as_view(), name='register'),
    path('change_password/<str:id>',
         UpdatePasswordView.as_view(), name='update_password'),
    path('login', AuthView.as_view(), name='login'),
    path('password_request', PasswordRequestView.as_view(), name="password_request"),
    path('restore_password', RestorePasswordView.as_view(), name="restore_password"),
]
