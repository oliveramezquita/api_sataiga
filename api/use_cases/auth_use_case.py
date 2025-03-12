from datetime import datetime
from api.helpers.http_responses import ok, bad_request
from api.helpers.bcrypt import encrypt_password, verify_password
from api.helpers.validations import email_validation
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.serializers.user_serializer import UserSerializer
from api_sataiga.functions import encode_user, hex_decode, hex_encode, send_email
from bson import ObjectId
from django.conf import settings


class AuthUseCase:
    def __init__(self, data):
        self.data = data

    def __user_ability_rules(self, rules):
        user_ability_rules = []
        for rule, ability in rules.items():
            for i in ability:
                user_ability_rules.append({
                    'action': i,
                    'subject': rule
                })
        return user_ability_rules

    def __set_home(self, permissions):
        is_admin = [k for k, v in permissions.items(
        ) if k == 'AdminDashboard' and 'read' in v]
        if len(is_admin) > 0:
            return 'admin'
        return 'user'

    def login(self):
        with MongoDBHandler('users') as db:
            required_fields = ['email', 'password']
            if all(i in self.data for i in required_fields):
                user = db.extract({'email': self.data['email'], 'status': 1})
                if user:
                    if verify_password(self.data['password'], user[0]['password']):
                        user_ability_rules = self.__user_ability_rules(
                            user[0]['permissions'])
                        permissions = user[0]['permissions']
                        user = UserSerializer(user[0]).data
                        user.pop('permissions')
                        return ok({
                            'userAbilityRules': user_ability_rules,
                            'accessToken': encode_user(user),
                            'userData': user,
                            'home': self.__set_home(permissions)
                        })
                    return bad_request('Usuario o contraseña no son válidos.')
                return bad_request('Usuario no encontrado')
            return bad_request('El correo electrónico y la contraseña son obligatorios.')

    def password_request(self):
        with MongoDBHandler('password_request') as db:
            if 'email' in self.data and email_validation(self.data['email']):
                user = MongoDBHandler.find(
                    db, 'users', {'email': self.data['email']})
                if user:
                    user_id = str(user[0]['_id'])
                    password_request = db.extract(
                        {'user_id': user_id})
                    if password_request:
                        db.delete({'user_id': user_id})
                    db.insert({
                        'user_id': user_id,
                        'hash_request': hex_encode({
                            'id': user_id,
                            'datetime': datetime.now().isoformat()})
                    })
                    send_email(
                        template="mail_templated/restore_password.html",
                        context={
                            'subject': 'Restauración de Contraseña del Sistema Bellarti',
                            'full_name': user[0]['name'] + f' {user[0]['lastname']}' if user[0]['lastname'] else '',
                            'email': user[0]['email'],
                            'link_href': settings.ADMIN_URL,
                            'link_label': 'RESTAURAR CONTRASEÑA'
                        },
                    )
                    return ok('La solicitud para el cambio de contrasela ha sido enviada.')
                return bad_request('El correo electrónico no se encuentra registrado.')
            return bad_request('El correo electrónico no es válido.')

    def restore_password(self):
        with MongoDBHandler('users') as db:
            required_fields = ['hash_request', 'password', 'confirm_password']
            if all(i in self.data for i in required_fields):
                payload = hex_decode(self.data['hash_request'])
                password_request = MongoDBHandler.find(
                    db, 'password_request', {'user_id': payload['id']})
                if password_request:
                    difference = datetime.now() - \
                        password_request[0]['created_at'].replace(tzinfo=None)
                    hours_difference = difference.total_seconds() / 3600
                    if int(hours_difference) < 25:
                        if self.data['password'] == self.data['confirm_password']:
                            password = encrypt_password(
                                self.data['password'])
                            db.update({'_id': payload['id']}, {
                                'password': password})
                            MongoDBHandler.remove(db, 'password_request', {
                                '_id': ObjectId(password_request[0]['_id'])})
                            return ok('La contraseña ha sido restaurada correctamente.')
                        return bad_request('Las contraseñas no coinciden.')
                    return bad_request('Se venció el tiempo para procesar la restauración de la contrasela. Solicite una nueva solicitud de cambio de contraeña.')
                return bad_request('Ocurrió un error al procesar la restauración de la contraseña. Solicite una nueva solicitud de cambio de contraeña.')
            return bad_request('Algunos campos requeridos no han sido completados.')
