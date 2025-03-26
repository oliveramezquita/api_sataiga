from pymongo import MongoClient
from django.conf import settings
from datetime import datetime


class MongoDBHandler:
    def __init__(self, collection_name):
        self.client = None
        self.db = None
        self.collection_name = collection_name

    def __enter__(self):
        uri = "mongodb://{}:{}@{}:{}?authSource=admin".format(
            settings.MONGO_DB['USER'],
            settings.MONGO_DB['PASS'],
            settings.MONGO_DB['HOST'],
            settings.MONGO_DB['PORT'])
        self.client = MongoClient(uri)
        self.db = self.client[settings.MONGO_DB['NAME']]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    def insert(self, data):
        collection = self.db[self.collection_name]
        data['created_at'] = datetime.now()
        data['updated_at'] = datetime.now()
        result = collection.insert_one(data)
        return result.inserted_id

    def extract(self, query=None):
        collection = self.db[self.collection_name]
        result = collection.find(query)
        return list(result)

    def update(self, query, update_data):
        collection = self.db[self.collection_name]
        update_data['updated_at'] = datetime.now()
        _ = collection.update_one(query, {'$set': update_data})
        result = collection.find(query)
        return list(result)

    def delete(self, query):
        collection = self.db[self.collection_name]
        result = collection.delete_one(query)
        return result.deleted_count

    def create_unique_index(self, field):
        collection = self.db[self.collection_name]
        collection.create_index([(field, 1)], unique=True)

    @staticmethod
    def find(inst, collection_name, query):
        collection = inst.db[collection_name]
        result = collection.find(query)
        return list(result)

    @staticmethod
    def modify(inst, collection_name, query, modify_data):
        collection = inst.db[collection_name]
        modify_data['updated_at'] = datetime.now()
        result = collection.update_one(query, {'$set': modify_data})
        return result.modified_count

    @staticmethod
    def remove(inst, collection_name, query):
        collection = inst.db[collection_name]
        result = collection.delete_one(query)
        return result.deleted_count
