import logging
import datetime
from django.contrib.auth.hashers import check_password, make_password
from api.models.user import User, PasswordRequest
from api.helpers.http_response import ok, bad_request
from api.helpers.validations import email_validation
from sataiga_api.functions import encode_user, hex_encode, hex_decode
from api.serializers.user_serializer import UserSerializer
from django.db.models import Max

log = logging.getLogger(__name__)


class AuthUseCase:
    def __init__(self, data):
        self.data = data

    def login(self):
        user = User.objects.filter(email=self.data['email'], status=1).first()
        if user:
            if check_password(self.data['password'], user.password):
                try:
                    user = UserSerializer(user).data
                    return ok({
                        'userAbilityRules': user['role_value'],
                        'accessToken': encode_user(user),
                        'userData': user
                    })
                except Exception as e:
                    log.error(e.args[0])
                    return bad_request(e.args[0])
            return bad_request('Usuario o contraseña no son válidos.')
        return bad_request('Usuario no encontrado')

    def password_request(self):
        if 'email' in self.data and email_validation(self.data['email']):
            user = User.objects.filter(email=self.data['email']).first()
            if user:
                user_serializer = UserSerializer(user).data
                password_request = PasswordRequest.objects.filter(
                    user_id=user_serializer['id']).first()
                last_request = PasswordRequest.objects.aggregate(Max('id'))[
                    'id__max']
                if password_request:
                    password_request.delete()
                PasswordRequest(
                    user=user,
                    hash_request=hex_encode({
                        'id': user_serializer['id'],
                        'datetime': datetime.datetime.now().isoformat(),
                        'last_request': last_request if last_request else 1})
                ).save()
                # TODO: Enviar correo con la liga para la restauración de la contraseña
                return ok('La solicitud para el cambio de contrasela ha sido enviada.')
            return bad_request('El correo electrónico no se encuentra registrado.')
        return bad_request('El correo electrónico no es válido.')

    def restore_password(self):
        required_fields = ['hash_request', 'password', 'confirm_password']
        if all(i in self.data for i in required_fields):
            payload = hex_decode(self.data['hash_request'])
            log.info(payload)
            password_request = PasswordRequest.objects.filter(
                user_id=payload['id']).first()
            if password_request:
                difference = datetime.datetime.now(
                ) - password_request.created_at.replace(tzinfo=None)
                hours_difference = difference.total_seconds() / 3600
                if int(hours_difference) < 25:
                    if self.data['password'] == self.data['confirm_password']:
                        try:
                            password = make_password(self.data['password'])
                            User.objects.filter(id=payload['id']).update(
                                password=password)
                            password_request.delete()
                            return ok('La contraseña ha sido restaurada correctamente.')
                        except Exception as e:
                            log.error(e.args[0])
                            return bad_request(e.args[0])
                    return bad_request('Las contraseñas no coinciden.')
                return bad_request('Se venció el tiempo para procesar la restauración de la contrasela. Solicite una nueva solicitud de cambio de contraeña.')
            return bad_request('Ocurrió un error al procesar la restauración de la contraseña. Solicite una nueva solicitud de cambio de contraeña.')
        return bad_request('Algunos campos requeridos no han sido completados.')
