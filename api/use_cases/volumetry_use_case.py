import re
import traceback
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.validations import objectid_validation
from bson import ObjectId
from api.helpers.http_responses import bad_request, ok, not_found
from api.serializers.volumetry_serializer import VolumetrySerializer
from api.serializers.file_serializer import FileUploadSerializer
from urllib.parse import parse_qs
from openpyxl import load_workbook
from api.functions.quantify import quantify


class VolumetryUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            self.request = request
            params = parse_qs(request.META['QUERY_STRING'])
            self.client_id = params['client_id'][0] if 'client_id' in params else None
            self.front = params['front'][0] if 'front' in params else None

        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def __client_validation(self, db):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            self.data['client_id']), 'type': 'VS'}) if objectid_validation(self.data['client_id']) else None
        if client:
            return client[0]
        return False

    def __material_validation(self, db):
        material = MongoDBHandler.find(db, 'materials', {'_id': ObjectId(
            self.data['material_id'])}) if objectid_validation(self.data['material_id']) else None
        if material:
            return material
        return False

    def __check_prototypes(self):
        with MongoDBHandler('prototypes') as db:
            prototypes = db.extract(
                {'client_id': self.client_id, 'front': self.front})
            if prototypes:
                return [item["name"] for item in prototypes]
            return False

    def __sanitize_data(self, data):
        if data.get('total') == '' or data.get('total') is None:
            data['total'] = 0

        for proto in data.get('prototypes', []):
            quantities = proto.get('quantities', {})
            for key in ['factory', 'instalation']:
                if quantities.get(key) == '' or quantities.get(key) is None:
                    quantities[key] = 0
                elif isinstance(quantities[key], str) and quantities[key].isdigit():
                    quantities[key] = int(quantities[key])
        return data

    def __calculate_totals(self):
        gran_total = 0
        pattern = re.compile(r'^\d+(\.\d{1,2})?$')
        for i, item in enumerate(self.data['volumetry']):
            self.data['volumetry'][i] = self.__sanitize_data(item)
            total = sum(
                float(q) if isinstance(q, (int, float, str)) and pattern.match(
                    str(q)) else 0
                for prototype in item['prototypes']
                for q in prototype['quantities'].values()
            )
            item['total'] = total
            gran_total += total

        self.data['gran_total'] = gran_total
        return self.data

    def __get_prototypes(self):
        with MongoDBHandler('prototypes') as db:
            prototypes = db.extract(
                {'client_id': self.client_id, 'front': self.front})
            if prototypes:
                return sorted(set(item["name"] for item in prototypes))
            return []

    def __get_id_material_by_name(self, **kwargs):
        with MongoDBHandler('materials') as db:
            filters = {
                'concept': kwargs.get('concept'),
                'measurement': kwargs.get('measurement'),
            }
            if kwargs.get('sku'):
                filters['sku'] = kwargs.get('sku')
            material = db.extract(filters)
            if material:
                return str(material[0]['_id'])
            return False

    def __process_workbook(self, workbook, existing_prototypes):
        result = []
        warnings = []
        error = None
        prototypes = workbook.sheetnames

        all_materials = []
        try:
            for sheet_name in prototypes:
                if sheet_name not in existing_prototypes:
                    warnings.append(
                        f'El prototipo: {sheet_name} no se encuentra registrado con el cliente y el frente seleccionados.')
                    continue

            for sheet_name in existing_prototypes:
                sheet = workbook[sheet_name]
                for row_index in range(2, sheet.max_row + 1):
                    material = sheet[f"A{row_index}"].value
                    if material:
                        material_id = self.__get_id_material_by_name(
                            concept=material,
                            measurement=sheet[f"B{row_index}"].value,
                            sku=sheet[f"C{row_index}"].value,
                        )
                        if not material_id:
                            warnings.append(
                                f'El material: {material} no existe en la base de datos, verifique el nombre así como la unidad de medida y el código del proveedor.')
                        if material_id and not any(material_id in materials.values() for materials in all_materials):
                            all_materials.append(
                                {'_id': material_id, 'name': material})

            for material in all_materials:
                material_data = {
                    "material_id": material['_id'],
                    "reference": None,
                    "volumetry": [],
                    "gran_total": 0
                }
                volumetry_by_area = {}

                for prototype_name in existing_prototypes:
                    sheet = workbook[prototype_name]
                    for row_index in range(2, sheet.max_row + 1):
                        if sheet[f"A{row_index}"].value == material['concept']:
                            material_data["reference"] = sheet[f"D{row_index}"].value

                            col_index = 5
                            while True:
                                header_cell = sheet.cell(
                                    row=1, column=col_index).value
                                if header_cell is None:
                                    break
                                parts = header_cell.split('-')
                                if len(parts) == 2:
                                    area = parts[0].strip()

                                    if area not in volumetry_by_area:
                                        volumetry_by_area[area] = {
                                            "prototypes": {}}

                                    if prototype_name not in volumetry_by_area[area]["prototypes"]:
                                        volumetry_by_area[area]["prototypes"][prototype_name] = {
                                            "quantities": {"factory": 0, "instalation": 0}}

                                    value = sheet.cell(
                                        row=row_index, column=col_index).value
                                    quantity = float(value) if isinstance(
                                        value, (int, float)) else 0

                                    if col_index % 2:
                                        volumetry_by_area[area]["prototypes"][prototype_name]["quantities"]["factory"] = quantity
                                    else:
                                        volumetry_by_area[area]["prototypes"][
                                            prototype_name]["quantities"]["instalation"] = quantity
                                else:
                                    warnings.append(
                                        f"La columna: {header_cell} no tiene el formato correcto: 'ÁREA - FÁBRICA' o 'ÁREA - INSTALACIÓN'")
                                col_index += 1
                            break

                total_gran_material = 0
                for area, data in volumetry_by_area.items():
                    area_total = 0
                    prototype_list = []
                    for proto_name in existing_prototypes:
                        quantities = data["prototypes"].get(
                            proto_name, {"quantities": {"factory": 0, "instalation": 0}})
                        factory_qty = quantities["quantities"].get(
                            "factory", 0)
                        instalation_qty = quantities["quantities"].get(
                            "instalation", 0)
                        prototype_list.append({
                            "prototype": proto_name,
                            "quantities": {
                                "factory": factory_qty,
                                "instalation": instalation_qty
                            }
                        })
                        area_total += factory_qty + instalation_qty

                    material_data["volumetry"].append({
                        "area": area,
                        "prototypes": prototype_list,
                        "total": round(area_total, 2)
                    })
                    total_gran_material += area_total
                material_data["gran_total"] = round(total_gran_material, 2)
                result.append(material_data)
        except Exception as e:
            error = str(e)
        return result, list(set(warnings)), error

    def __process_data(self, volumetry_data):
        updated = 0
        inserted = 0
        with MongoDBHandler('volumetries') as db:
            for item in volumetry_data:
                is_exist = db.extract(
                    {'client_id': self.client_id, 'front': self.front, 'material_id': item['material_id']})
                material = self.__material_validation(db)
                if self.__client_validation(db) and material:
                    if is_exist:
                        db.update({
                            'client_id': self.client_id,
                            'front': self.front,
                            'material_id': item['material_id']},
                            {
                                'volumetry': item['volumetry'],
                                'gran_total': item['gran_total'],
                        })
                        updated += 1
                    else:
                        db.insert({
                            'client_id': self.client_id,
                            'front': self.front,
                            'supplier_id': material[0]['supplier_id'],
                            **item
                        })
                        inserted += 1
        return inserted, updated

    def __extract(self):
        with MongoDBHandler('volumetries') as db:
            return db.extract(
                {'client_id': self.client_id, 'front': self.front})

    def save(self):
        with MongoDBHandler('volumetries') as db:
            required_fields = ['client_id',
                               'front', 'material_id', 'volumetry']
            if all(i in self.data for i in required_fields):
                material = self.__material_validation(db)
                if self.__client_validation(db) and material:
                    is_exist = db.extract(
                        {'client_id': self.data['client_id'], 'front': self.data['front'], 'material_id': self.data['material_id']})
                    if is_exist:
                        db.update({
                            'client_id': self.data['client_id'],
                            'front': self.data['front'],
                            'material_id': self.data['material_id']},
                            self.__calculate_totals())
                        message = f'El material: {material[0]['concept']} ha sido actualizado correctamente en la volumetría.'
                    else:
                        db.insert({
                            'supplier_id': material[0]['supplier_id'],
                            **self.__calculate_totals()})
                        message = f'El material: {material[0]['concept']} ha sido añadido correctamente en la volumetría.'
                    volumetries = db.extract({
                        'client_id': self.data['client_id'],
                        'front': self.data['front']})
                    quantify.delay(self.data['client_id'], self.data['front'])
                    return ok({'data': VolumetrySerializer(volumetries, many=True).data, 'message': message})
                return bad_request('Error al momento de procesar la información: el cliente o el material no existen.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        if self.client_id and self.front:
            volumetry = self.__extract()
            return ok({
                'volumetry': VolumetrySerializer(volumetry, many=True).data,
                'prototypes': self.__get_prototypes(),
            })
        return not_found('No existe volumería con lo datos asignados.')

    def delete(self):
        with MongoDBHandler('volumetries') as db:
            volumetry = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if volumetry:
                db.delete({'_id': ObjectId(self.id)})
                return ok('El área en la volumetría ha sido eliminado correctamente.')
            return bad_request('El área en la volumetría no existe.')

    def upload(self):
        prototypes = self.__check_prototypes()
        if not prototypes:
            return bad_request('No existen prototipos para el cliente y el frente seleccionados.')

        serializer = FileUploadSerializer(data=self.data)
        if serializer.is_valid():
            excel_file = self.request.FILES['file']
            try:
                workbook = load_workbook(excel_file, data_only=True)
                volumetry_data, warnings, error = self.__process_workbook(
                    workbook, prototypes)
                num_inserted, num_updated = self.__process_data(volumetry_data)

                volumetry = []
                if num_inserted > 0 or num_updated > 0:
                    volumetry = VolumetrySerializer(
                        self.__extract(), many=True).data

                return ok({
                    'num_inserted': num_inserted,
                    'num_updated': num_updated,
                    'warnings': warnings,
                    'error': error,
                    'volumetry': volumetry,
                })
            except Exception as e:
                return bad_request(f'Error: {str(e)}, "Trace": {traceback.format_exc()}')
        return bad_request(serializer.errors)
