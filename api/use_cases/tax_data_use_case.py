import os
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.validations import objectid_validation
from bson import ObjectId
from api.helpers.http_responses import bad_request, ok
from api.serializers.tax_data_serializer import TaxDataSerializer
from django.core.files.storage import FileSystemStorage
from rest_framework import exceptions
from api_sataiga.settings import BASE_URL


class TaxDataUseCase:
    def __init__(self, request=None, **kwargs):
        self.data = kwargs.get('data', None)
        self.supplier_id = kwargs.get('supplier_id', None)
        self.client_id = kwargs.get('client_id', None)

    def __check_supplier(self, db):
        supplier = MongoDBHandler.find(db, 'suppliers', {'_id': ObjectId(
            self.supplier_id)}) if objectid_validation(self.supplier_id) else None
        if supplier:
            return True
        return False

    def __check_client(self, db):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            self.client_id)}) if objectid_validation(self.client_id) else None
        if client:
            return True
        return False

    def __upload_constancy(self):
        constancy = self.data['constancy']
        fs = FileSystemStorage(
            location='media/certificates', base_url='media/certificates')
        filename = f'media/certificates/{constancy.name}'
        if os.path.exists(filename):
            os.remove(filename)

        ext = os.path.splitext(constancy.name)[1]
        if not ext.lower() in ['.pdf']:
            raise exceptions.ValidationError(
                "El archivo no tiene el formato correcto."
            )

        filename = fs.save(constancy.name, constancy)
        uploaded_file_url = fs.url(filename)
        return f"{BASE_URL}/{uploaded_file_url}"

    def __check_rfc(self, rfc):
        with MongoDBHandler('tax_data') as db:
            tax_data = db.extract(
                {'supplier_id': self.supplier_id, 'rfc': rfc})
            if tax_data:
                return True
            return False

    def __is_url_pdf(self):
        if isinstance(self.data['constancy'], str) and (self.data['constancy'].startswith("http://") or self.data['constancy'].startswith("https://")):
            return self.data['constancy'].endswith(".pdf")
        return False

    def save_by_supplier(self):
        with MongoDBHandler('tax_data') as db:
            required_fields = ['rfc', 'name']
            data = {key: value for key, value in self.data.items()}
            if all(i in data for i in required_fields):
                data['supplier_id'] = self.supplier_id
                if 'constancy' in data and not self.__is_url_pdf():
                    data['constancy'] = self.__upload_constancy()

                if self.__check_supplier(db):
                    if self.__check_rfc(data['rfc']):
                        db.update(
                            {'supplier_id': self.supplier_id, 'rfc': data['rfc']}, data)
                    else:
                        db.insert(data)
                    return ok('Los datos fiscales han sigo guardados con éxito.')
                return bad_request('El proveedor selecionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get_by_supplier(self):
        with MongoDBHandler('tax_data') as db:
            tax_data = db.extract({'supplier_id': self.supplier_id})
            if tax_data:
                return ok(TaxDataSerializer(tax_data[0]).data)
            return ok({'rfc': ''})

    def save_by_client(self):
        with MongoDBHandler('tax_data') as db:
            data = {key: value for key, value in self.data.items()}
            if 'name' in self.data:
                data['client_id'] = self.client_id
                if 'constancy' in data and not self.__is_url_pdf():
                    data['constancy'] = self.__upload_constancy()

                if self.__check_client(db):
                    if self.__check_rfc(data['rfc']):
                        db.update(
                            {'client_id': self.client_id, 'rfc': data['rfc']}, data)
                    else:
                        db.insert(data)
                    return ok('Los datos fiscales han sigo guardados con éxito.')
                return bad_request('El cliente selecionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get_by_client(self):
        with MongoDBHandler('tax_data') as db:
            tax_data = db.extract({'client_id': self.client_id})
            if tax_data:
                return ok(TaxDataSerializer(tax_data[0]).data)
            return ok({})
