from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import redis
from pymongo import MongoClient


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        status = {"api": "ok"}

        # Redis
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                socket_connect_timeout=1
            )
            r.ping()
            status["redis"] = "ok"
        except Exception:
            status["redis"] = "error"

        # Mongo
        try:
            uri = f"mongodb://{settings.MONGO_DB['USER']}:{settings.MONGO_DB['PASS']}@{settings.MONGO_DB['HOST']}:{settings.MONGO_DB['PORT']}/?authSource=admin"
            client = MongoClient(uri, serverSelectionTimeoutMS=1000)
            client.server_info()
            status["mongo"] = "ok"
        except Exception:
            status["mongo"] = "error"

        return Response(status)
