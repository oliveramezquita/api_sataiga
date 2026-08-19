from typing import Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta
from api.services.base_service import BaseService
from api.repositories.customer_repository import CustomerRepository
from api.helpers.clean_payload import clean_payload
from api.serializers.customer_serializer import CustomerSerializer


class CustomerService(BaseService):
    """Lógica de negocio pura para los clientes de Postventa."""

    CACHE_PREFIX = "customers"

    def __init__(self):
        self.customer_repo = CustomerRepository()

    def create(self, data: dict):
        warranty = {}

        if warranty_data := data.pop('warranty', None):
            duration = float(warranty_data.get('duration', 0))

            warranty = {
                'id': warranty_data.get('_id'),
                'expiration_date': datetime.today() + relativedelta(
                    months=round(duration * 12)
                ),
                'status': 1,
            }

        self._create(
            repo=self.customer_repo,
            data=clean_payload({**data, 'warranty': warranty, 'status': 0}),
            required_fields=["name", "address", "email",
                             "phone", "project"],
            cache_prefix=self.CACHE_PREFIX,
        )

    def get_paginated(self,
                      warranty_type: Optional[str] = None,
                      q: Optional[str] = None,
                      page: int = 1,
                      page_size: int = 10,
                      sort_by: str = None,
                      order_by: int = 1):
        filters = {}
        if warranty_type:
            filters['warranty.id'] = warranty_type
        if q:
            filters["$or"] = [
                {"name": {"$regex": q, "$options": "i"}},
                {"last_name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}},
                {"phone": {"$regex": q, "$options": "i"}},
            ]
        items = self._get_all_cached(
            self.customer_repo, filters,
            prefix=self.CACHE_PREFIX,
            order_field=sort_by,
            order=order_by)
        return self._paginate(items, page, page_size, serializer=CustomerSerializer)

    def get_by_id(self, customer_id: str):
        return self._get_by_id(self.customer_repo, customer_id, serializer=CustomerSerializer)

    def update(self, customer_id: str, data: dict):
        payload = clean_payload(data)
        self._update(self.customer_repo, customer_id, payload,
                     cache_prefix=self.CACHE_PREFIX)

    def delete(self, customer_id: str):
        self._update(self.customer_repo, customer_id, {
                     'status': 0}, cache_prefix=self.CACHE_PREFIX)
