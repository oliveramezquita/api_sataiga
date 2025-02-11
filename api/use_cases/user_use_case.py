import logging
from api.models.user import User, Role
from api.helpers.http_response import *
from api.helpers.validations import email_validation
from api.serializers.user_serializer import UserSerializer
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import exceptions
from urllib.parse import parse_qs
from api.static import DEFAULT_PAGE_SIZE
from django.core.paginator import Paginator

log = logging.getLogger(__name__)


class UserUseCase:
    def __init__(self, request=None, data=None, id=None):
        params = parse_qs(request.META['QUERY_STRING'])
        self.page = params['page'][0] if 'page' in params else 1
        self.page_size = params['itemsPerPage'][0] \
            if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
        self.data = data
        self.id = id

    def save(self):
        required_fields = ['role', 'name', 'email']
        if all(i in self.data for i in required_fields):
            self._validate_params()
            try:
                role = Role.objects.get(id=self.data['role'])
                User(
                    role=role,
                    name=self.data['name'],
                    lastname=self.data['lastname'],
                    email=self.data['email'],
                ).save()
                # TODO: Enviar correo con la liga para registrar
                return created('Usuario creado correctamente.')
            except Exception as e:
                log.error(e.args[0])
                return bad_request(e.args[0])
        return bad_request('Algunos campos requeridos no han sido completados.')

    def _validate_params(self):
        if 'email' in self.data:
            users = User.objects.filter(email=self.data['email'], status__lt=2)
            if users:
                raise exceptions.ValidationError(
                    "El correo electrónico proporcionado ya ha sido registrado. Por favor, utilice una dirección de correo electrónico diferente."
                )

            if not email_validation(self.data['email']):
                raise exceptions.ValidationError(
                    "La dirección de correo electrónico proporcionada no es correcta."
                )

        if 'role' in self.data:
            role = Role.objects.filter(id=self.data['role'])
            if not role:
                raise exceptions.ValidationError(
                    "El rol seleccionado no se encuentra registrado en el sistema."
                )

    def get(self):
        users = User.objects.filter(status__lt=2)
        paginator = Paginator(users, per_page=self.page_size)
        page = paginator.get_page(self.page)
        return ok_paginated(
            paginator,
            page,
            UserSerializer(page.object_list, many=True).data
        )

    def get_by_id(self):
        user = User.objects.filter(id=self.id, status__lt=2).first()
        if user:
            return ok(UserSerializer(user).data)
        return not_found('El usuario no se existe.')

    def register(self):
        user = User.objects.filter(id=self.id).first()
        if user and user.status == 0:
            required_fields = ['password', 'confirm_password']
            if all(i in self.data for i in required_fields):
                if self.data['password'] == self.data['confirm_password']:
                    try:
                        password = make_password(self.data['password'])
                        User.objects.filter(id=self.id).update(
                            password=password, status=1)
                        return ok('Registro realizado exitosamente.')
                    except Exception as e:
                        log.error(e.args[0])
                        return bad_request(e.args[0])
                return bad_request('Las contraseñas no coinciden.')
            return bad_request('Algunos campos requeridos no han sido completados.')
        return bad_request('El usaurio no existe o ya se encuentra activado.')

    def update(self):
        user = User.objects.filter(id=self.id).first()
        if user and user.status < 2:
            self._validate_params()
            try:
                User.objects.filter(id=self.id).update(**self.data)
                return ok('Usuario actualizado correctamente.')
            except Exception as e:
                log.error(e.args[0])
                return bad_request(e.args[0])
        return bad_request('El usaurio no existe.')

    def update_password(self):
        user = User.objects.filter(id=self.id, status=1).first()
        required_fields = ['old_password', 'new_password', 'confirm_password']
        if user and all(i in self.data for i in required_fields):
            if check_password(self.data['old_password'], user.password):
                if self.data['new_password'] == self.data['confirm_password']:
                    try:
                        password = make_password(self.data['new_password'])
                        User.objects.filter(id=self.id).update(
                            password=password)
                        return ok('Su contraeña ha sido actualizada.')
                    except Exception as e:
                        log.error(e.args[0])
                        return bad_request(e.args[0])
                return bad_request('Las contraseña nueva y su confirmación no coinciden.')
            return bad_request('La contraseña actual es incorrecta. Intoduzca su contraseña actual para hacer el cambio de contraseña.')
        return bad_request('No ha sido posible cambiar la contraseña. Verifique que no haya campos faltantes y que el usuario se encuentre registrado.')

    def delete(self):
        user = User.objects.filter(id=self.id).first()
        if user and user.status < 2:
            try:
                User.objects.filter(id=self.id).update(status=2)
                return ok('Usuario eliminado correctamente.')
            except Exception as e:
                log.error(e.args[0])
                return bad_request(e.args[0])
        return bad_request('El usaurio no existe o ya se encuentra eliminado.')
