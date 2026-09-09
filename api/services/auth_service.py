from typing import Any
from bson import ObjectId
from django.conf import settings
from rest_framework.exceptions import ValidationError
from api.services.base_service import BaseService
from api.repositories.auth_repository import AuthRepository
from api_sataiga.functions import send_email
from api.utils.cache_utils import invalidate_cache


class AuthService(BaseService):
    """
    Lógica de negocio para manejar la autenticación
    de clientes y técnicos de postventa.
    """

    def __init__(self):
        self.repo = AuthRepository()

    def create(
        self,
        user_type: str,
        user_name: str,
        user_data: dict[str, Any],
    ):
        if user_type not in ("customer", "technician"):
            raise ValidationError(
                'El tipo de usuario debe ser "customer" o "technician".'
            )

        data = {
            "user_id": user_data.get("user_id"),
            "user_type": user_type,
            "email": user_data.get("email"),
            "phone": user_data.get("phone"),
            "password": None,
            "status": 0,
            "failed_login_attempts": 0,
            "locked_until": None,
            "password_changed_at": None,
            "activated_at": None,
            "last_login": None,
            "last_login_ip": None
        }

        self._create(
            repo=self.repo,
            data=data,
            required_fields=[
                "user_id",
                "user_type",
                "email",
                "phone",
            ],
        )
        self.send_invitation(user_name, data['email'])

    def get(self, user_type: str, user_id: str):
        if user_type and user_id:
            projection = {
                'email': 1,
                'phone': 1,
                'status': 1,
                'failed_login_attempts': 1,
                'password_changed_at': 1,
                'activated_at': 1,
                'last_login': 1,
            }
            return self.repo.find_one(
                query={'user_type': user_type, 'user_id': ObjectId(user_id)},
                projection=projection
            )
        return None

    def manage_status(self, user_type: str, user_id: str, status: int, cache_prefx=None):
        query = {
            'user_type': user_type,
            'user_id': ObjectId(user_id)
        }
        self.repo.update_one(query=query, update_data={'status': status})

        if cache_prefx:
            invalidate_cache(cache_prefx)

    @staticmethod
    def send_invitation(name: str, email: str):
        email = email.strip() if email else None

        if not email:
            raise ValidationError(
                'El correo electrónico es obligatorio para enviar la invitación.'
            )

        name = name.strip() if name else email

        send_email(
            template="mail_templated/send_invitation.html",
            context={
                'subject': 'Descarga BellartiMovil y comienza a utilizar nuestros servicios',
                'name': name,
                'app_store_url': '',
                'app_store_image_url': f"{settings.BASE_URL}/media/images/appstore.png",
                'play_store_url': '',
                'play_store_image_url': f"{settings.BASE_URL}/media/images/googleplay.png",
            },
            to=[email],
        )
