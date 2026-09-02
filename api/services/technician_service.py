from typing import Optional
from api.services.base_service import BaseService
from api.helpers.clean_payload import clean_payload
from api.repositories.technician_repository import TechnicianRepository
from api.serializers.technician_serializer import TechnicianSerializer


class TechnicianService(BaseService):
    """Lógica de negocio pura para los técnicos de Postventa."""

    CACHE_PREFIX = "technicians"

    def __init__(self):
        self.technician_repo = TechnicianRepository()

    def create(self, data: dict):
        schedule = {'monday': [], 'tuesday': [], 'wednesday': [],
                    'thursday': [], 'friday': [], 'saturday': []}
        self._create(
            repo=self.technician_repo,
            data=clean_payload(
                {**data, 'schedule': schedule, 'blocked_dates': [], 'status': 0}),
            required_fields=["name", "email", "phone"],
            cache_prefix=self.CACHE_PREFIX,
        )

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
                {"last_name": {"$regex": q, "$options": "i"}},
                {"email": {"$regex": q, "$options": "i"}},
                {"phone": {"$regex": q, "$options": "i"}},
            ]
        items = self._get_all_cached(
            self.technician_repo, filters,
            prefix=self.CACHE_PREFIX,
            order_field=sort_by,
            order=order_by)
        return self._paginate(items, page, page_size, serializer=TechnicianSerializer)

    def get_by_id(self, technician_id: str):
        return self._get_by_id(self.technician_repo, technician_id, serializer=TechnicianSerializer)

    def update(self, technician_id: str, data: dict):
        payload = clean_payload(data)
        data = payload.get('info')
        schedule = payload.get('schedule')
        blocked_dates = payload.get('blocked_dates')

        if schedule:
            data['schedule'] = self._convert_schedule(schedule)

        if blocked_dates:
            data['blocked_dates'] = self._convert_blocked_dates(blocked_dates)

        self._update(self.technician_repo, technician_id,
                     data, cache_prefix=self.CACHE_PREFIX)

    def delete(self, technician_id: str):
        self._update(self.technician_repo, technician_id, {
                     'status': 0}, cache_prefix=self.CACHE_PREFIX)

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
