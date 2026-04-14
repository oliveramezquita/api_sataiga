from pymongo import ReturnDocument
from django.conf import settings
from datetime import datetime
from .mongo_client import get_mongo_client


class MongoDBHandler:
    def __init__(self, collection_name):
        self.client = None
        self.db = None
        self.collection_name = collection_name

    def __enter__(self):
        self.client = get_mongo_client()
        self.db = self.client[settings.MONGO_DB['NAME']]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def insert(self, data):
        collection = self.db[self.collection_name]
        data['created_at'] = datetime.now()
        data['updated_at'] = datetime.now()
        result = collection.insert_one(data)
        return result.inserted_id

    def extract(self, query=None, order_field=None, order=1, projection=None):
        collection = self.db[self.collection_name]
        if projection:
            result = collection.find(query, projection)
        else:
            result = collection.find(query)
        if order_field:
            result = result.sort(order_field, order)
        return list(result)

    def update(self, query, update_data, upsert=False):
        collection = self.db[self.collection_name]
        now = datetime.now()

        # Normalizar a operadores
        if any(k.startswith('$') for k in update_data.keys()):
            ops = update_data
        else:
            ops = {'$set': update_data}

        # updated_at siempre
        ops.setdefault('$set', {})
        ops['$set']['updated_at'] = now

        # created_at solo en insert (upsert)
        if upsert:
            ops.setdefault('$setOnInsert', {})
            ops['$setOnInsert']['created_at'] = now

        # Doc final
        doc = collection.find_one_and_update(
            query,
            ops,
            upsert=upsert,
            return_document=ReturnDocument.AFTER,
        )
        return doc

    def delete(self, query):
        collection = self.db[self.collection_name]
        result = collection.delete_many(query)
        return result.deleted_count

    def create_unique_index(self, field):
        collection = self.db[self.collection_name]
        collection.create_index([(field, 1)], unique=True)

    def get_next_folio(self, element):
        collection = self.db['counters']
        result = collection.find_one({"_id": element})
        if result:
            return result["seq"] + 1
        return 1

    def set_next_folio(self, element):
        collection = self.db['counters']
        result = collection.find_one_and_update(
            {"_id": element},
            {"$inc": {"seq": 1}},
            return_document=ReturnDocument.AFTER,
            upsert=True
        )
        return result["seq"]

    @staticmethod
    def find(inst, collection_name, query, order_field=None, order=1, projection=None):
        collection = inst.db[collection_name]
        if projection:
            result = collection.find(query, projection)
        else:
            result = collection.find(query)
        if order_field:
            result = result.sort(order_field, order)
        return list(result)

    @staticmethod
    def record(inst, collection_name, data):
        collection = inst.db[collection_name]
        data['created_at'] = datetime.now()
        data['updated_at'] = datetime.now()
        result = collection.insert_one(data)
        return result.inserted_id

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
