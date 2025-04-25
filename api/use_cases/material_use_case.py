from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, ok_paginated, not_found
from bson import ObjectId
from api.helpers.validations import objectid_validation
from django.core.paginator import Paginator
from api.serializers.material_serializer import MaterialSerializer
from api.serializers.file_serializer import FileUploadSerializer
from openpyxl import load_workbook
from decimal import Decimal, InvalidOperation
from rest_framework import exceptions


class MaterialUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.status = params['status'][0] if 'status' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def __check_supplier(self, db):
        supplier = MongoDBHandler.find(db, 'suppliers', {'_id': ObjectId(
            self.data['supplier_id'])}) if objectid_validation(self.data['supplier_id']) else None
        if supplier:
            return True
        return False

    def __process_workbook(self, workbook):
        sheet = workbook.active

        data = []
        errors = []

        for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            row_errors = []

            def get_decimal(value, field_name):
                try:
                    if value is None or value == '':
                        return None
                    convert = Decimal(str(value)).quantize(Decimal('0.01'))
                    return str(convert)
                except (InvalidOperation, ValueError):
                    row_errors.append(
                        f"Fila {idx}: '{field_name}' no es un número decimal válido.")
                    return None

            name = row[0]
            measurement = row[1]

            if not name or not measurement:
                row_errors.append(
                    f"Fila {idx}: 'NOMBRE / DESCRIPCIÓN' y 'UNIDAD DE MEDIDA' son obligatorios.")

            record = {
                "supplier_id": self.data['supplier_id'],
                "name": str(name).strip() if name else '',
                "measurement": str(measurement).strip() if measurement else '',
                "supplier_code": str(row[2]).strip() if row[2] else None,
                "internal_code": str(row[3]).strip() if row[3] else None,
                "presentation": str(row[4]).strip() if row[4] else None,
                "area": str(row[5]).strip() if row[5] else None,
                "reference": str(row[6]).strip() if row[6] else None,
                "minimum": get_decimal(row[7], "MÍNIMOS DE STOCK"),
                "maximum": get_decimal(row[8], "MÁXIMOS DE STOCK"),
                "unit_price": get_decimal(row[9], "PRECIO UNIDAD"),
                "inventory_price": get_decimal(row[10], "PRECIO PRESENTACIÓN"),
                "market_price": get_decimal(row[11], "PRECIO MERCADO"),
                "price_difference": get_decimal(row[12], "DIFERENCIA DE PRECIO")
            }

            if row_errors:
                errors.append({"fila": idx, "errores": row_errors})
            else:
                data.append(record)

        return data, errors

    def __process_materials(self, materials):
        with MongoDBHandler('materials') as db:
            inserted = []
            updated = []
            if self.__check_supplier(db):
                for item in materials:
                    material = db.extract({
                        'supplier_id': item['supplier_id'],
                        'name': item['name'],
                        'measurement': item['measurement'],
                    })
                    if material:
                        db.update({'_id': ObjectId(material[0]['_id'])}, item)
                        updated.append(item['name'])
                    else:
                        db.insert(item)
                        inserted.append(item['name'])
                return inserted, updated
            raise exceptions.NotFound('El proveedor seleccionado no existe.')

    def save(self):
        with MongoDBHandler('materials') as db:
            required_fields = ['name', 'supplier_id', 'measurement']
            if all(i in self.data for i in required_fields):
                if self.__check_supplier(db):
                    if 'automation' not in self.data:
                        self.data['automation'] = False
                    id = db.insert(self.data)
                    return created({'id': str(id)})
                return bad_request('El proveedor selecionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('materials') as db:
            materials = db.extract()
            paginator = Paginator(materials, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                MaterialSerializer(page.object_list, many=True).data
            )

    def get_by_id(self):
        with MongoDBHandler('materials') as db:
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material:
                return ok(MaterialSerializer(material[0]).data)
            return not_found('El material no existe.')

    def update(self):
        with MongoDBHandler('materials') as db:
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material:
                if 'supplier_id' in self.data and not self.__check_supplier(db):
                    return bad_request('El proveedor selecionado no existe.')
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('Material actualizado correctamente.')
            return bad_request('El material no existe.')

    def delete(self):
        with MongoDBHandler('materials') as db:
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Material eliminado correctamente.')
            return bad_request('El material no existe.')

    def upload(self):
        required_fields = ['supplier_id', 'file']
        data = {key: value for key, value in self.data.items()}
        if all(i in data for i in required_fields):
            serializer = FileUploadSerializer(data=self.data)
            if serializer.is_valid():
                excel_file = self.data['file']
                try:
                    workbook = load_workbook(excel_file, data_only=True)
                    materials, errors = self.__process_workbook(workbook)
                    inserted, updated = self.__process_materials(materials)
                    return ok({
                        "message": f"Materiales procesados correctamente: {len(inserted)} insertados, {len(updated)} atualizados y hubó {len(errors)} errores.",
                        "inserted": inserted,
                        "updated": updated,
                        "errors": errors,
                    })
                except Exception as e:
                    return bad_request(f'Error: {str(e)}')
            return bad_request('Error al momento de cargar el arhivo Excel.')
        return bad_request('El proveedor así como el archivo en formaro Excel son requeridos.')
