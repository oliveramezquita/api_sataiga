from api.helpers.http_responses import ok, bad_request
from api_sataiga.handlers.mongodb_handler import MongoDBHandler


class DashboardUseCase:
    def __get_user_status_overview(self):
        with MongoDBHandler('users') as db:
            users = db.extract()
            status_counts = [0, 0, 0]

            for user in users:
                status = user.get('status')
                if status in (0, 1, 2):
                    status_counts[status] += 1

            return [status_counts, len(users)]

    def get(self):
        dashboard_data = []
        dashboard_data.append(
            {'users_status': self.__get_user_status_overview()})
        return ok(dashboard_data)
