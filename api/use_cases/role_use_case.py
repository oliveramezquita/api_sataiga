import logging
from api.models.user import Role
from api.helpers.http_response import ok, created, bad_request
from api.serializers.role_serializer import RoleSerializer


log = logging.getLogger(__name__)


class RoleUseCase:
    def __init__(self, data=None, id=None):
        self.data = data
        self.id = id

    def save(self):
        required_fields = ['name', 'value']
        if all(i in self.data for i in required_fields):
            try:
                Role(
                    name=self.data['name'],
                    value=self.data['value'],
                ).save()
                return created('Rol creado correctamente.')
            except Exception as e:
                log.error(e.args[0])
                return bad_request(e.args[0])
        return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        roles = Role.objects.all()
        return ok(RoleSerializer(roles, many=True).data)

    def update(self):
        role = Role.objects.filter(id=self.id).first()
        if role:
            try:
                Role.objects.filter(id=self.id).update(**self.data)
                return ok('Rol actualizado correctamente.')
            except Exception as e:
                log.error(e.args[0])
                return bad_request(e.args[0])
        return bad_request('El rol no existe')
