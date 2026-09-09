from typing import Optional
from datetime import datetime
from bson import ObjectId
from api.services.base_service import BaseService
from api.services.auth_service import AuthService
from api.helpers.clean_payload import clean_payload
from api.repositories.technician_repository import TechnicianRepository
from api.serializers.technician_serializer import TechnicianSerializer
from api.helpers.review_required_fields import review_required_fields
from api.utils.cache_utils import invalidate_cache


class TechnicianService(BaseService):
    """Lógica de negocio pura para los técnicos de Postventa."""

    CACHE_PREFIX = "technicians"

    default_projection = {
        "_id": 1,
        "name": 1,
        "schedule": 1,
        "blocked_dates": 1,
        "is_deleted": 1,
        "email": "$auth.email",
        "phone": "$auth.phone",
        "status": "$auth.status",
    }

    def __init__(self):
        self.technician_repo = TechnicianRepository()
        self.auth_service = AuthService()

    def create(self, data: dict):
        required_fields = {
            "name": str,
            "email": str,
            "phone": str,
        }

        review_required_fields(required_fields, data)

        schedule = {'monday': [], 'tuesday': [], 'wednesday': [],
                    'thursday': [], 'friday': [], 'saturday': []}

        user_data = {
            "name": data.get("name"),
            "schedule": schedule,
            "blocked_dates": [],
            "is_deleted": False,
            "deleted_at": None
        }

        user_id = self._create(
            repo=self.technician_repo,
            data=clean_payload(user_data),
            required_fields=["name"],
        )
        self.auth_service.create(
            "technician",
            data.get("name"),
            {
                "user_id": user_id,
                "email": data.get("email"),
                "phone": data.get("phone"),
            }
        )

        invalidate_cache(self.CACHE_PREFIX)

    def get_paginated(self,
                      q: Optional[str] = None,
                      page: int = 1,
                      page_size: int = 10,
                      sort_by: str = None,
                      order_by: int = 1):
        filters = {}

        if q:
            filters["$or"] = [
                {"name": {"$regex": q, "$options": "i"}},
            ]

        technicians = self._get_all_aggregated_cached(
            repo=self.technician_repo,
            filters=filters,
            prefix=self.CACHE_PREFIX,
            ttl=300,
            order_field=sort_by or "name",
            order=order_by,
            projection=self.default_projection
        )

        return self._paginate(
            technicians,
            page,
            page_size,
            serializer=TechnicianSerializer
        )

    def get_by_id(self, technician_id: str):
        return self.technician_repo.find_one_with_auth(
            query={
                "_id": ObjectId(technician_id)
            },
            projection=self.default_projection,
            serializer=TechnicianSerializer
        )

    def update(self, technician_id: str, data: dict):
        payload = clean_payload(data)
        data = payload.get('info')
        schedule = payload.get('schedule')
        blocked_dates = payload.get('blocked_dates')

        if schedule:
            data['schedule'] = self._convert_schedule(schedule)

        if blocked_dates:
            data['blocked_dates'] = self._convert_blocked_dates(blocked_dates)

        self._update(
            self.technician_repo,
            technician_id,
            data,
            cache_prefix=self.CACHE_PREFIX
        )

    def delete(self, technician_id: str):
        self._update(
            self.technician_repo,
            technician_id,
            {
                "is_deleted": True,
                "deleted_at": datetime.today()
            },
            cache_prefix=self.CACHE_PREFIX
        )

    @staticmethod
    def _convert_schedule(schedule: dict) -> dict:
        return {
            day: [
                {
                    "start": start,
                    "end": end,
                }
                for start, end in (
                    slot.split("-", 1)
                    for slot in sorted(times)
                )
            ]
            for day, times in schedule.items() if times
        }

    @staticmethod
    def _convert_blocked_dates(dates: str) -> list[str]:
        return [
            date.strip()
            for date in dates.split(",")
            if date.strip()
        ]
