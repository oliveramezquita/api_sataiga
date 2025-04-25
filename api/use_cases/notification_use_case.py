from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from urllib.parse import parse_qs
from datetime import datetime, timedelta
from api.serializers.notification_serializer import NotificationSerializer
from api.helpers.http_responses import ok, bad_request
from bson import ObjectId
from api.helpers.validations import objectid_validation


class NotificationUseCase:
    def __init__(self, request=None, data=None):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.user_id = params['user_id'][0] if 'user_id' in params else None
            self.role = params['role'][0] if 'role' in params else None
            self.today = params['today'][0] if 'today' in params else None
        self.data = data

    def get(self):
        with MongoDBHandler('notifications') as db:
            filters = {
                "$or": [
                    {"user_id": self.user_id},
                    {"roles": self.role}
                ],
            }
            if self.today:
                filters['created_at'] = {
                    "$gte": datetime.strptime(self.today, "%Y-%m-%d"),
                    "$lt": datetime.strptime(self.today, "%Y-%m-%d") + timedelta(days=1)
                }
            notifications = db.extract(filters)
            return ok(NotificationSerializer(notifications, many=True).data)

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
