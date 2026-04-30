from api.utils.pagination_utils import DummyPaginator, DummyPage
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.get_query_params import get_query_params
from api.helpers.http_responses import ok, ok_paginated, bad_request
from bson import ObjectId
from api.helpers.validations import objectid_validation
from api.services.notification_service import NotificationService


class NotificationUseCase:
    def __init__(self, request=None, data=None):
        params = get_query_params(request)
        self.q = params["q"]
        self.page = params["page"]
        self.page_size = params["page_size"]
        self.sort_by = params["sort_by"]
        self.order_by = params["order_by"]
        self.user_id = params.get('user_id')
        self.role = params.get('role')
        self.today = params.get('today')
        self.data = data
        self.service = NotificationService()

    def get(self):
        """Método especial con paginación manual."""
        try:
            roles = self.role if isinstance(self.role, list) else [self.role]
            filters = {
                "$or": [
                    {"user_id": self.user_id},
                    {"roles": {"$in": roles}},
                ]
            }
            result = self.service.get_paginated(
                filters, self.page, self.page_size, self.sort_by, self.order_by
            )
            dummy_paginator = DummyPaginator(
                result["count"], result["total_pages"])
            dummy_page = DummyPage(
                result["current_page"], dummy_paginator, result["results"])
            return ok_paginated(dummy_paginator, dummy_page, result["results"])
        except Exception as e:
            return bad_request(f"Error al obtener las notificaciones: {e}")

    def update(self):
        with MongoDBHandler('notifications') as db:
            updated = []
            for notification_id in self.data['notifications']:
                notification = db.extract(
                    {'_id': ObjectId(notification_id)}) if objectid_validation(notification_id) else None
                if notification:
                    db.update({'_id': ObjectId(notification_id)},
                              {'is_seen': self.data['is_seen'] if 'is_seen' in self.data else False})
                    updated.append(notification_id)
            return ok(f'{len(updated)} notificaciones actualizadas.')

    def delete(self):
        with MongoDBHandler('notifications') as db:
            if 'notification' in self.data:
                notification = db.extract(
                    {'_id': ObjectId(self.data['notification'])}) if objectid_validation(self.data['notification']) else None
                if notification:
                    db.delete({'_id': ObjectId(self.data['notification'])})
                    return ok('Notificación eliminada correctamente.')
            return bad_request('La o las actualizacion(es) no existe(n).')
