# mongo_client.py
from pymongo import MongoClient
from django.conf import settings

_client = None


def get_mongo_client():
    global _client
    if _client is None:
        uri = "mongodb://{}:{}@{}:{}?authSource=admin".format(
            settings.MONGO_DB['USER'],
            settings.MONGO_DB['PASS'],
            settings.MONGO_DB['HOST'],
            settings.MONGO_DB['PORT']
        )
        _client = MongoClient(uri)
    return _client
