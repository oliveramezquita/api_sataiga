import os
import traceback
from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import created, bad_request, ok, ok_paginated, not_found
from bson import ObjectId
from api.helpers.validations import objectid_validation
from django.core.paginator import Paginator
from api.serializers.material_serializer import MaterialSerializer
from api.serializers.file_serializer import FileUploadSerializer
from openpyxl import load_workbook, Workbook
from decimal import Decimal, InvalidOperation
from rest_framework import exceptions
from django.http import HttpResponse
from PIL import Image
from django.conf import settings
from api.functions.concept_n_sku import generate_concept_and_sku


class MaterialUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            self.request = request
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
            self.supplier = params['supplier'][0] if 'supplier' in params else None
            self.division = params['division'][0] if 'division' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.supplier_id = kwargs.get('supplier_id', None)

    def __check_supplier(self, db):
        supplier = MongoDBHandler.find(db, 'suppliers', {'_id': ObjectId(
            self.data['supplier_id'])}) if objectid_validation(self.data['supplier_id']) else None
        if supplier:
            return True
        return False

    def __valid_value(self, data, idx):
        if len(data) <= idx:
            return None

        not_valid = ['', 'None']
        if not data[idx] or data[idx] in not_valid:
            return None

        if not isinstance(data[idx], str):
            return str(data[idx]).strip()

        return data[idx].strip()

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

            division = row[0]
            name = row[1]
            measurement = row[7]

            if not division or not name or not measurement:
                row_errors.append(
                    f"Fila {idx}: 'DIVISIÓN', 'MATERIAL' y 'UNIDAD DE MEDIDA' son obligatorios.")

            record = {
                "supplier_id": self.data['supplier_id'],
                "division": division.strip() if division else '',
                "name": name.strip() if name else '',
                "espec1": self.__valid_value(row, 2),
                "espec2": self.__valid_value(row, 3),
                "espec3": self.__valid_value(row, 4),
                "espec4": self.__valid_value(row, 5),
                "espec5": self.__valid_value(row, 6),
                "measurement": measurement.strip() if measurement else '',
                "supplier_code": self.__valid_value(row, 8),
                "presentation": self.__valid_value(row, 9),
                "area": self.__valid_value(row, 10),
                "reference": self.__valid_value(row, 11),
                "minimum": get_decimal(row[12], "MÍNIMOS DE STOCK"),
                "maximum": get_decimal(row[13], "MÁXIMOS DE STOCK"),
                "unit_price": get_decimal(row[14], "PRECIO UNIDAD"),
                "inventory_price": get_decimal(row[15], "PRECIO PRESENTACIÓN"),
                "market_price": get_decimal(row[16], "PRECIO MERCADO"),
                "price_difference": get_decimal(row[17], "DIFERENCIA DE PRECIO"),
                "automation": len(row) > 18 and str(row[18]) == 'SI'
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
                    filters = {
                        'supplier_id': item['supplier_id'],
                        'division': item['division'],
                        'name': item['name'],
                        'measurement': item['measurement'],
                    }
                    for f in ['espec1', 'espec2', 'espec3', 'espec4', 'espec5', 'supplier_code', 'presentation']:
                        if f in item and item[f]:
                            filters[f] = item[f]
                    material = db.extract(filters)
                    if material:
                        if 'sku' not in material[0] or not material[0]['sku']:
                            concept, sku = generate_concept_and_sku(
                                material[0])
                            item['concept'] = concept
                            item['sku'] = sku
                        db.update({'_id': ObjectId(material[0]['_id'])}, item)
                        updated.append(
                            item['concept'] if 'concept' in item else material[0]['concept'])
                    else:
                        concept, sku = generate_concept_and_sku(item)
                        item['concept'] = concept
                        item['sku'] = sku
                        db.insert(item)
                        inserted.append(item['concept'])
                return inserted, updated
            raise exceptions.NotFound('El proveedor seleccionado no existe.')

    def __suppliers_list(self):
        with MongoDBHandler('suppliers') as db:
            suppliers_list = {}
            suppliers = db.extract()
            if suppliers:
                for supplier in suppliers:
                    suppliers_list[str(supplier['_id'])] = supplier['name']
            return suppliers_list

    def __validate_value(self, material, key):
        if key in material:
            return material[key]
        return None

    def __export_materials(self, materials):
        suppliers_list = self.__suppliers_list()
        wb = Workbook()
        ws = wb.active
        ws.title = "Materiales"

        headers = [
            'PROVEEDOR', 'CONCEPTO', 'UNIDAD DE MEDIDA', 'CÓDIGO PROVEEDOR',
            'SKU', 'PRESENTACIÓN', 'ÁREA', 'REFERENCIA',
            'MÍNIMOS DE STOCK', 'MÁXIMOS DE STOCK',
            'PRECIO UNIDAD', 'PRECIO PRESENTACIÓN', 'PRECIO MERCADO', 'DIFERENCIA DE PRECIO'
        ]
        ws.append(headers)

        for material in materials:
            ws.append([
                suppliers_list[material['supplier_id']],
                material['concept'],
                material['measurement'],
                self.__validate_value(material, 'supplier_code'),
                self.__validate_value(material, 'sku'),
                self.__validate_value(material, 'presentation'),
                self.__validate_value(material, 'area'),
                self.__validate_value(material, 'reference'),
                float(self.__validate_value(material, 'minimum') or 0),
                float(self.__validate_value(material, 'maximum') or 0),
                float(self.__validate_value(material, 'unit_price') or 0),
                float(self.__validate_value(material, 'invetory_price') or 0),
                float(self.__validate_value(material, 'market_price') or 0),
                float(self.__validate_value(material, 'price_difference') or 0),
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=materiales.xlsx'
        wb.save(response)
        return response

    def save(self):
        with MongoDBHandler('materials') as db:
            required_fields = ['division', 'name',
                               'concept', 'measurement', 'supplier_id', 'sku']
            if all(i in self.data for i in required_fields):
                if self.__check_supplier(db):
                    if 'automation' not in self.data:
                        self.data['automation'] = False
                    material_id = db.insert(self.data)
                    return created({'id': str(material_id)})
                return bad_request('El proveedor selecionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('materials') as db:
            filters = {}
            if self.q:
                filters['$or'] = [
                    {'concept': {'$regex': self.q, '$options': 'i'}},
                    {'measurement': {'$regex': self.q, '$options': 'i'}},
                    {'supplier_code': {'$regex': self.q, '$options': 'i'}},
                    {'sku': {'$regex': self.q, '$options': 'i'}},
                    {'presentation': {'$regex': self.q, '$options': 'i'}},
                    {'reference': {'$regex': self.q, '$options': 'i'}},
                ]
            if self.supplier:
                filters['supplier_id'] = self.supplier
            materials = db.extract(filters)
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

    def get_by_supplier(self):
        with MongoDBHandler('materials') as db:
            filter_query = {
                "supplier_id": self.supplier_id
            }

            if self.division and len(self.division) > 0:
                filter_query["division"] = {"$in": self.division.split(',')}

            materials = db.extract(filter_query)
            if materials:
                return ok(MaterialSerializer(materials, many=True).data)
            return ok([])

    def update(self):
        with MongoDBHandler('materials') as db:
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material:
                if 'supplier_id' in self.data and not self.__check_supplier(db):
                    return bad_request('El proveedor selecionado no existe.')
                updated = db.update({'_id': ObjectId(self.id)}, self.data)
                return ok(MaterialSerializer(updated[0]).data)
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
        data = dict(self.data.items())
        if all(i in data for i in required_fields):
            serializer = FileUploadSerializer(data=self.data)
            if serializer.is_valid():
                excel_file = self.data['file']
                try:
                    workbook = load_workbook(excel_file, data_only=True)
                    materials, errors = self.__process_workbook(workbook)
                    inserted, updated = self.__process_materials(materials)
                    return ok({
                        "message": f"Materiales procesados correctamente: {len(inserted)} insertado(s), {len(updated)} atualizado(s) y hubó {len(errors)} error(es).",
                        "inserted": inserted,
                        "updated": updated,
                        "errors": errors,
                    })
                except Exception as e:
                    return bad_request(f'Error: {str(e)}, "Trace": {traceback.format_exc()}')
            return bad_request('Error al momento de cargar el arhivo Excel.')
        return bad_request('El proveedor así como el archivo en formaro Excel son requeridos.')

    def download(self):
        with MongoDBHandler('materials') as db:
            filters = {}
            if self.q:
                filters['$or'] = [
                    {'concept': {'$regex': self.q, '$options': 'i'}},
                    {'measurement': {'$regex': self.q, '$options': 'i'}},
                    {'supplier_code': {'$regex': self.q, '$options': 'i'}},
                    {'sku': {'$regex': self.q, '$options': 'i'}},
                    {'presentation': {'$regex': self.q, '$options': 'i'}},
                    {'reference': {'$regex': self.q, '$options': 'i'}},
                ]
            if self.supplier:
                filters['supplier_id'] = self.supplier
            materials = db.extract(filters)
            return self.__export_materials(materials)

    def upload_image(self):
        with MongoDBHandler('materials') as db:
            images = []
            image = self.request.FILES['image']
            material = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if material and image:
                if 'images' in material[0]:
                    images = material[0]['images']

                img = Image.open(image)
                if img.format not in ['JPEG', 'PNG']:
                    return bad_request('El archivo cargado no es una imagen valida.')

                material_folder = os.path.join(
                    settings.MEDIA_ROOT, 'materials/' + str(self.id))
                os.makedirs(material_folder, exist_ok=True)

                image_path = os.path.join(material_folder, image.name)

                with open(image_path, 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)

                relative_path = f"{settings.BASE_URL}/media/materials/{str(self.id)}/{image.name}"
                images.append(relative_path)

                db.update({'_id': ObjectId(self.id)}, {'images': images})

                return ok(images)
            return bad_request('El material no existe.')

    def delete_image(self):
        with MongoDBHandler('materials') as db:
            if 'images' in self.data:
                material = db.extract(
                    {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
                if material:
                    if 'images' in material[0] and isinstance(self.data['images'], list):
                        deleted = []
                        for idx in self.data['images']:
                            deleted.append(material[0]['images'][idx])
                            relative_path = material[0]['images'][idx].replace(
                                settings.BASE_URL, '')
                            file_path = os.path.join(
                                settings.BASE_DIR, relative_path.strip('/'))
                            if os.path.isfile(file_path):
                                os.remove(file_path)

                        new_images = [url for url in material[0]
                                      ['images'] if url not in deleted]
                        db.update({'_id': ObjectId(self.id)}, {
                            'images': new_images})
                        return ok(new_images)
                    return bad_request('No existen imágenes en el material seleccionado y/o las imágenes seleccionadas para eliminar.')
                return bad_request('El material no existe.')
            return bad_request('Falta el índice de la imagen para poder eliminarla.')
