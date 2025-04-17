from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.validations import objectid_validation
from bson import ObjectId
from api.helpers.http_responses import bad_request, ok
from api.serializers.bank_data_serializer import BankDataSerializer


class BankDataUseCase:
    def __init__(self, request=None, **kwargs):
        self.data = kwargs.get('data', None)
        self.supplier_id = kwargs.get('supplier_id', None)

    def __check_supplier(self, db):
        supplier = MongoDBHandler.find(db, 'suppliers', {'_id': ObjectId(
            self.supplier_id)}) if objectid_validation(self.supplier_id) else None
        if supplier:
            return True
        return False

    def save(self):
        with MongoDBHandler('bank_data') as db:
            required_fields = ['account_number', 'card_number', 'clabe']
            if self.data['bank'] and any(i in self.data for i in required_fields):
                if self.__check_supplier(db):
                    is_exists = db.extract({'supplier_id': self.supplier_id})
                    if len(is_exists) > 0:
                        db.update({'supplier_id': self.supplier_id}, self.data)
                    else:
                        self.data['supplier_id'] = self.supplier_id
                        db.insert(self.data)
                    return ok('Los datos bancarios han sigo guardados con éxito.')
                return bad_request('El proveedor selecionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get_by_supplier(self):
        with MongoDBHandler('bank_data') as db:
            bank_data = db.extract({'supplier_id': self.supplier_id})
            if bank_data:
                return ok(BankDataSerializer(bank_data[0]).data)
            return ok({})
