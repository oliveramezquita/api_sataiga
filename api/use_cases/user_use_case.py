import logging
from urllib.parse import parse_qs
from rest_framework import exceptions
from api.constants import DEFAULT_PAGE_SIZE
from api.helpers.validations import email_validation, objectid_validation
from api.serializers.user_serializer import UserSerializer
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api_sataiga.functions import send_email, hex_encode
from api.helpers.http_responses import *
from django.core.paginator import Paginator
from bson import ObjectId
from pymongo import errors
from api.helpers.bcrypt import encrypt_password, verify_password
from django.conf import settings


log = logging.getLogger(__name__)


class UserUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def __validate_params(self, db):
        if 'email' in self.data and not email_validation(self.data['email']):
            raise exceptions.ValidationError(
                "La dirección de correo electrónico proporcionada no es correcta.")

        if 'role' in self.data and objectid_validation(self.data['role_id']):
            role = MongoDBHandler.find(
                db, 'roles', {'_id': ObjectId(self.data['role_id'])})
            if not role:
                raise exceptions.ValidationError(
                    "El rol seleccionado no se encuentra registrado en el sistema.")

    def save(self):
        with MongoDBHandler('users') as db:
            required_fields = ['role_id', 'name', 'email']
            if all(i in self.data for i in required_fields):
                self.__validate_params(db)
                try:
                    db.create_unique_index('email')
                    self.data['status'] = 0
                    user_id = db.insert(self.data)
                    hash_request = hex_encode({
                        'id': str(user_id),
                        'email': self.data['email']
                    })
                    send_email(
                        template="mail_templated/register.html",
                        context={
                            'subject': 'Invitación para el registro del Sistema Bellarti',
                            'full_name': self.data['name'] + f' {self.data['lastname']}' if 'lastname' in self.data else '',
                            'email': self.data['email'],
                            'link_href': f"{settings.ADMIN_URL}register?hr={hash_request}",
                            'link_label': 'REGISTRAR'
                        },
                    )
                    return created('Usuario creado correctamente.')
                except errors.DuplicateKeyError:
                    return bad_request('El correo electrónico proporcionado ya ha sido registrado. Por favor, utilice una dirección de correo electrónico diferente.')
                except Exception as e:
                    log.error(e.args[0])
                    return error(e.args[0])
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('users') as db:
            users = db.extract({'status': {'$lt': 2}})
            paginator = Paginator(users, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                UserSerializer(page.object_list, many=True).data
            )

    def register(self):
        with MongoDBHandler('users') as db:
            user = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if user and user[0]['status'] == 0:
                required_fields = ['password', 'confirm_password']
                if all(i in self.data for i in required_fields):
                    if self.data['password'] == self.data['confirm_password']:
                        try:
                            password = encrypt_password(self.data['password'])
                            db.update({'_id': ObjectId(self.id)}, {
                                      'password': password, 'status': 1})
                            send_email(
                                template="mail_templated/activated.html",
                                context={
                                    'subject': '¡Registro Completo! Bienvenido al Sistema Bellarti',
                                    'full_name': user[0]['name'] + f' {user[0]['lastname']}' if user[0]['lastname'] else '',
                                    'email': user[0]['email'],
                                    'link_href': settings.ADMIN_URL,
                                    'link_label': 'INICIAR SESIÓN'
                                },
                            )
                            return ok('Registro realizado exitosamente.')
                        except Exception as e:
                            log.error(e.args[0])
                            return error(e.args[0])
                    return bad_request('Las contraseñas no coinciden.')
                return bad_request('Algunos campos requeridos no han sido completados.')
            return bad_request('El usaurio no existe o ya se encuentra registrado.')

    def get_by_id(self):
        with MongoDBHandler('users') as db:
            user = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if user:
                return ok(UserSerializer(user[0]).data)
            return not_found('El usuario no se existe.')

    def update(self):
        with MongoDBHandler('users') as db:
            user = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if user and user[0]['status'] < 2:
                self.__validate_params(db)
                try:
                    db.update({'_id': ObjectId(self.id)}, self.data)
                    return ok('Usuario actualizado correctamente.')
                except Exception as e:
                    log.error(e.args[0])
                    return error(e.args[0])
            return bad_request('El usaurio no existe.')

    def update_password(self):
        with MongoDBHandler('users') as db:
            user = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            required_fields = ['old_password',
                               'new_password', 'confirm_password']
            if user and all(i in self.data for i in required_fields):
                if verify_password(self.data['old_password'], user[0]['password']):
                    if self.data['new_password'] == self.data['confirm_password']:
                        try:
                            password = encrypt_password(
                                self.data['new_password'])
                            db.update({'_id': ObjectId(self.id)},
                                      {'password': password})
                            return ok('Su contraeña ha sido actualizada.')
                        except Exception as e:
                            log.error(e.args[0])
                            return error(e.args[0])
                    return bad_request('Las contraseña nueva y su confirmación no coinciden.')
                return bad_request('La contraseña actual es incorrecta. Intoduzca su contraseña actual para hacer el cambio de contraseña.')
            return bad_request('No ha sido posible cambiar la contraseña. Verifique que no haya campos faltantes y que el usuario se encuentre registrado.')

    def delete(self):
        with MongoDBHandler('users') as db:
            user = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if user and user[0]['status'] < 2:
                try:
                    db.update({'_id': ObjectId(self.id)}, {'status': 2})
                    return ok('Usuario eliminado correctamente.')
                except Exception as e:
                    log.error(e.args[0])
                    return error(e.args[0])
            return bad_request('El usaurio no existe o ya se encuentra eliminado.')
