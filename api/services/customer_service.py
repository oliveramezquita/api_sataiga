from typing import Any, Optional
from datetime import datetime
from bson import ObjectId
from dateutil.relativedelta import relativedelta
from api.services.base_service import BaseService
from api.services.auth_service import AuthService
from api.repositories.customer_repository import CustomerRepository
from api.helpers.clean_payload import clean_payload
from api.serializers.customer_serializer import CustomerSerializer
from api.helpers.review_required_fields import review_required_fields


class CustomerService(BaseService):
    """Lógica de negocio pura para los clientes de Postventa."""

    CACHE_PREFIX = "customers"

    def __init__(self):
        self.customer_repo = CustomerRepository()
        self.auth_service = AuthService()

    def create(self, data: dict):
        required_fields = {
            "project": Any,
            "warranty": Any,
            "name": str,
            "email": str,
            "phone": str,
            "address": str,
        }

        review_required_fields(required_fields, data)

        project = data.pop('project', None)

        warranty = {}

        if warranty_data := data.pop('warranty', None):
            expiration_date = data.pop('expiration_date', None)
            duration = float(warranty_data.get('duration', 0))
            months = round(duration * 12)

            expiration_date = (
                datetime.strptime(expiration_date, "%Y-%m-%d")
                if expiration_date
                else (
                    datetime.today() + relativedelta(months=months)
                ).replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
            )

            warranty = {
                'id': warranty_data.get('_id'),
                'expiration_date': expiration_date,
                'start_date': (
                    expiration_date
                    - relativedelta(months=months)
                ),
                'status': 1,
            }

        user_data = {
            "project": {
                key: value
                for key, value in project.items()
                if value is not None
            },
            "warranty": warranty,
            "name": data.get("name"),
            "address": data.get("address"),
            "is_deleted": False,
            "deleted_at": None
        }

        user_id = self._create(
            repo=self.customer_repo,
            data=clean_payload(user_data),
            required_fields=[
                "project",
                "warranty",
                "name",
                "address"
            ],
            cache_prefix=self.CACHE_PREFIX,
        )

        self.auth_service.create(
            "customer",
            data.get("name"),
            {
                "user_id": user_id,
                "email": data.get("email"),
                "phone": data.get("phone"),
            }
        )

    def get_paginated(
        self,
        warranty_type: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = None,
        order_by: int = 1
    ):
        filters = {}

        if warranty_type:
            filters['warranty.id'] = warranty_type

        if q:
            filters["$or"] = [
                {
                    "name": {
                        "$regex": q,
                        "$options": "i"
                    }
                },
                {
                    "address": {
                        "$regex": q,
                        "$options": "i"
                    }
                },
            ]

        customers = self._get_all_aggregated_cached(
            repo=self.customer_repo,
            filters=filters,
            prefix=f"{self.CACHE_PREFIX}_with_auth",
            ttl=300,
            order_field=sort_by or "name",
            order=order_by,
            projection={
                "_id": 1,
                "name": 1,
                "address": 1,
                "project": 1,
                "warranty": 1,
                "email": "$auth.email",
                "phone": "$auth.phone",
                "status": "$auth.status",
            }
        )

        return self._paginate(
            customers,
            page,
            page_size,
            serializer=CustomerSerializer
        )

    def get_by_id(self, customer_id: str):
        return self.customer_repo.find_one_with_auth(
            query={
                "_id": ObjectId(customer_id)
            },
            projection={
                "_id": 1,
                "name": 1,
                "address": 1,
                "project": 1,
                "warranty": 1,
                "email": "$auth.email",
                "phone": "$auth.phone",
                "status": "$auth.status",
            },
            serializer=CustomerSerializer
        )

    def update(self, customer_id: str, data: dict):
        payload = clean_payload(data)

        if warranty := payload.pop('warranty', None):
            start_date = warranty.get('start_date')
            expiration_date = warranty.get('expiration_date')
            duration = float(warranty.get('duration', 0))
            months = round(duration * 12)

            if expiration_date:
                warranty['expiration_date'] = datetime.fromisoformat(
                    expiration_date
                )
                warranty['start_date'] = (
                    warranty['expiration_date']
                    - relativedelta(months=months)
                )
            else:
                warranty['start_date'] = datetime.fromisoformat(
                    start_date
                )
                warranty['expiration_date'] = (
                    warranty['start_date']
                    + relativedelta(months=months)
                )

            warranty['status'] = (
                1
                if warranty['expiration_date'] > datetime.today().replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                else 0
            )

            warranty.pop('duration')

        self._update(
            self.customer_repo,
            customer_id,
            {
                **payload,
                'warranty': warranty
            },
            cache_prefix=self.CACHE_PREFIX
        )

    def delete(self, customer_id: str):
        self._update(
            self.customer_repo,
            customer_id,
            {
                "is_deleted": True,
                "deleted_at": datetime.today()
            },
            cache_prefix=self.CACHE_PREFIX
        )
