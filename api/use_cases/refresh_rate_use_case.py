import pytz
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId
from api.helpers.validations import objectid_validation
from api.helpers.http_responses import bad_request, ok, not_found
from api.serializers.refresh_rate_serializer import RefreshRateSerializer
from datetime import datetime
from api.functions.refresh_rates import refresh_rates


class RefreshRateUseCase:
    def __init__(self, request=None, **kwargs):
        self.data = kwargs.get('data', None)
        self.supplier_id = kwargs.get('supplier_id', None)
        self.current_timezone = pytz.timezone('America/Mexico_City')

    def __check_supplier(self, db, supplier_id):
        supplier = MongoDBHandler.find(db, 'suppliers', {'_id': ObjectId(
            supplier_id)}) if objectid_validation(supplier_id) else None
        if supplier:
            return True
        return False

    def save(self):
        with MongoDBHandler('regresh_rate') as db:
            if 'value' in self.data:
                if self.__check_supplier(db, self.supplier_id):
                    is_exists = db.extract({'supplier_id': self.supplier_id})
                    if len(is_exists) > 0:
                        db.update({'supplier_id': self.supplier_id}, self.data)
                    else:
                        self.data['supplier_id'] = self.supplier_id
                        db.insert(self.data)
                    return ok('Los frecuencia de actualización ha sido guardado con éxito.')
                return bad_request('El proveedor selecionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get_by_supplier(self):
        with MongoDBHandler('regresh_rate') as db:
            refresh_rate = db.extract({'supplier_id': self.supplier_id})
            if refresh_rate:
                return ok(RefreshRateSerializer(refresh_rate[0]).data)
            return ok({'value': None, 'next_date': datetime.now(self.current_timezone).strftime('%Y-%m-%d')})

    def refresh_rates(self):
        response = refresh_rates()
        if response:
            return ok(response)
        return bad_request('Hubó un error al procesar la información.')
