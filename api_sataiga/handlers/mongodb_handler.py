from pymongo import MongoClient
from django.conf import settings


class MongoDBHandler:
    def __init__(self):
        self.client = None
        self.db = None

    def __enter__(self):
        uri = "mongodb://{}:{}@{}:{}?authSource=admin".format(
            settings.MONGO_BD['USER'],
            settings.MONGO_BD['PASS'],
            settings.MONGO_BD['HOST'],
            settings.MONGO_BD['PORT'])
        self.client = MongoClient(uri)
        self.db = self.client[settings.MONGO_DB['NAME']]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    def insert(self, collection_name, data):
        collection = self.db[collection_name]
        result = collection.insert_one(data)
        return result.inserted_id

    def extract(self, collection_name, query):
        collection = self.db[collection_name]
        result = collection.find(query)
        return list(result)

    def update(self, collection_name, query, update_data):
        collection = self.db[collection_name]
        result = collection.update_one(query, {'$set': update_data})
        return result.modified_count

    def delete(self, collection_name, query):
        collection = self.db[collection_name]
        result = collection.delete_one(query)
        return result.deleted_count
