import copy
import math
import re
import traceback
import os
from collections import defaultdict
from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId
from api.helpers.validations import objectid_validation
from api.helpers.http_responses import created, bad_request, ok_paginated, ok, not_found
from api.constants import FIXED_PRESENTATIONS
from django.core.paginator import Paginator
from api.serializers.purchase_order_serializer import PurchaseOrderSerializer
from datetime import datetime
from django.conf import settings
from api.functions.oc_pdf import generate_pdf
from api.functions.oc_xlsx import create_xlsx
from api.use_cases.inbound_use_case import InboundUseCase
from api_sataiga.functions import send_notification
from api.helpers.get_message import get_message
from api.serializers.invoice_serializer import InvoiceUploadSerializer
from django.core.files.storage import FileSystemStorage
from api_sataiga.settings import BASE_URL
from rest_framework import exceptions
from api.serializers.supplier_serializer import SupplierSerializer


class PurchaseOrderUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
            self.q = params['q'][0] if 'q' in params else None
            self.project = params['project'][0] if 'project' in params else None
            self.supplier = params['supplier'][0] if 'supplier' in params else None
            self.status = params['status'][0] if 'status' in params else None
            self.division = params['division'][0] if 'division' in params else None
            self.type_project = params['type'][0] if 'type' in params else None
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.home_production_id = kwargs.get('home_production_id', None)
        self.supplier_id = kwargs.get('supplier_id', None)

    def __check_home_production(self, db, home_production_id):
        home_production = MongoDBHandler.find(db, 'home_production', {'_id': ObjectId(
            home_production_id)}) if objectid_validation(home_production_id) else None
        if home_production:
            return home_production[0]
        return False

    def __check_supplier(self, db, supplier_id):
        supplier = MongoDBHandler.find(db, 'suppliers', {'_id': ObjectId(
            supplier_id)}, 'name') if objectid_validation(supplier_id) else None
        if supplier:
            return supplier[0]
        return False

    def __check_client(self, db, client_id):
        client = MongoDBHandler.find(db, 'clients', {'_id': ObjectId(
            client_id)}) if objectid_validation(client_id) else None
        if client:
            return client[0]
        return False

    def __extract_material_fields(self, material):
        fields = [
            "concept", "measurement", "supplier_code", "unit_price",
            "inventory_price", "market_price", "price_difference",
            "automation", "images", "sku", "presentation",
            "reference", "division",
        ]

        retult = {}

        for field in fields:
            if field in material:
                retult[field] = material[field]

        return retult

    def __get_amount_presentation(self, presentation):
        if not presentation or presentation.strip() == "":
            return None

        presentation = presentation.upper()
        results = []
        for key, value in FIXED_PRESENTATIONS.items():
            if key == presentation:
                results.append(value)

        numbers = re.findall(r'\d+(?:\.\d+)?', presentation)
        if numbers:
            results.extend(float(n) if '.' in n else int(n) for n in numbers)

        results = sorted(set(results), key=lambda x: float(x))

        if not results:
            return None
        elif len(results) == 1:
            return results[0]
        else:
            return results

    def __get_total_automation(self, presentation, total, price):
        if not isinstance(presentation, list):
            total_quantity = math.ceil(total / presentation)
            return {
                'quantity': presentation,
                'total_quantity': total_quantity,
                'modified': 1,
                'total': round(float(total_quantity)*float(price), 2),
                'delivered': {
                    'rack': None,
                    'level': None,
                    'module': None,
                    'quantity': 0,
                    'registration_date': None
                },
            }
        else:
            # TODO: Por el momento sólo se tomará el primer valor de la presentación hasta saber como se manejará el precios
            total_quantity = math.ceil(total / presentation[0])
            return {
                'quantity': presentation[0],
                'total_quantity': total_quantity,
                'modified': 1,
                'total': round(float(total_quantity)*float(price), 2)
            }

    def __process_material_quantities(self, item, material):
        if ('presentation' in material and material['presentation']) and ('automation' in material and material['automation']):
            presentation = self.__get_amount_presentation(
                material['presentation'])
            return self.__get_total_automation(
                presentation,
                item['gran_total'],
                material['inventory_price'])
        return {
            'quantity': None,
            'total_quantity': item['gran_total'],
            'modified': 0,
            'total': round(float(item['gran_total'])*float(material['inventory_price']), 2),
            'delivered': {
                'rack': None,
                'level': None,
                'module': None,
                'quantity': 0,
                'registration_date': None
            },
        }

    def __process_material(self, db, item):
        material = MongoDBHandler.find(db, 'materials', {'_id': ObjectId(
            item['material_id'])}) if objectid_validation(item['material_id']) else None
        if material and (self.division is None or material[0].get('division') in self.division.split(',')):
            return {
                'material_id': item['material_id'],
                **self.__extract_material_fields(material[0]),
                **self.__process_material_quantities(item, material[0]),
            }
        return None

    def __format_location(self, data):
        parts = []

        if data.get('postal_code'):
            parts.append(f"CP. {data['postal_code']}")

        if data.get('city'):
            parts.append(data['city'])

        if data.get('state'):
            parts.append(data['state'])

        return ' '.join(parts)

    def __format_money(self, value):
        try:
            amount = float(value)
            return "$ {:,.2f}".format(amount)
        except (ValueError, TypeError):
            return value

    def __prepare_data_files(self, db, purchase_order):
        data = purchase_order
        data['client'] = ''
        data['location'] = ''
        data['company'] = []
        data['front'] = ''
        data['od'] = ''
        data['prototypes'] = ''

        # DATES
        if 'created' in data and data['created']:
            created_date = datetime.fromisoformat(
                data['created'].replace("Z", "+00:00"))
            data['created'] = created_date.strftime("%Y-%m-%d")
        estimated_delivery = datetime.fromisoformat(data['estimated_delivery'].replace(
            "Z", "+00:00")) if 'estimated_delivery' in data and data['estimated_delivery'] else None
        if estimated_delivery:
            data['estimated_delivery'] = estimated_delivery.strftime(
                "%Y-%m-%d")
        else:
            data['estimated_delivery'] = 'S/D'

        # HOME PRODUCTION
        home_production = self.__check_home_production(
            db, data['home_production_id'])
        if home_production:
            client = self.__check_client(
                db, home_production['client_id'])
            data['client'] = client['name'] if 'name' in client else ''
            front = home_production['front']
            data['front'] = front
            data['od'] = home_production['od']
            prototypes = home_production['lots']['prototypes']
            data['prototypes'] = prototypes
            prototypes_items = [f"{v} {k}" for k, v in prototypes.items()]
            data['location'] = 'front'
            if len(prototypes_items) == 1:
                data['location'] = f'{front} - {prototypes_items[0]}'
            else:
                data['location'] = f'{front} - ' + ', '.join(
                    prototypes_items[:-1]) + ' y ' + prototypes_items[-1]

        # COMPANY
        company = MongoDBHandler.find(db, 'companies', {'_id': ObjectId(
            data['company_id'])}) if objectid_validation(data['company_id']) else None
        if company and len(company) > 0:
            data['company'] = [company[0]['name']]
            if 'rfc' in company[0]:
                data['company'].append(f'RFC: {company[0]['rfc']}')
            if 'address' in company[0]:
                data['company'].append(company[0]['address'])
            if any(company[0].get(key) for key in ['rfc', 'city', 'state']):
                data['company'].append(self.__format_location(company[0]))
            if 'email' in company[0]:
                data['company'].append(company[0]['email'])

        # DIVISION
        data['division'] = ', '.join(data['division'])

        # MATERIALS
        data['materials'] = []
        for item in data['items']:
            data['materials'].append([
                item.get('supplier_code', ''),
                item.get('sku', ''),
                item.get('color', ''),
                item.get('total_quantity', 0),
                item.get('concept', ''),
                item.get('measurement', ''),
                item.get('inventory_price', 0),
                item.get('total', 0),
            ])

        # SUBTOTAL
        data['subtotal'] = [
            [self.__format_money(data.get('subtotal', 0))],
            [self.__format_money(data.get('discount', '-'))],
            [self.__format_money(data.get('iva', 0))],
        ]

        # TOTAL
        data['total'] = self.__format_money(data.get('total', 0))

        return data

    def __check_materials(self, db, materials):
        purchase_orders = MongoDBHandler.find(db, 'purchase_orders', {
                                              'home_production_id': self.home_production_id, 'supplier_id': self.supplier_id, 'status': {'$in': [1, 2]}})
        if purchase_orders:
            total_quantity_sum = defaultdict(float)

            for purchase_order in purchase_orders:
                for item in purchase_order['items']:
                    mat_id = item['material_id']
                    total_quantity_sum[mat_id] += float(
                        item.get('total_quantity', 0))

            result = []
            for material in materials:
                mat_id = material['material_id']
                required = float(material.get('required', 0))
                consumed = total_quantity_sum.get(mat_id, 0.0)
                diff = required - consumed

                if diff > 0:
                    new_item = copy.deepcopy(material)
                    new_item['total_quantity'] = diff
                    result.append(new_item)

            return result
        return materials

    def __upload_file(self, invoice_file, ext):
        fs = FileSystemStorage(
            location=f'media/purchase_orders/invoices/{self.id}',
            base_url=f'media/purchase_orders/invoices/{self.id}')
        filename = f'media/purchase_orders/invoices/{invoice_file.name}'
        if os.path.exists(filename):
            os.remove(filename)

        ext = os.path.splitext(invoice_file.name)[1]
        if not ext.lower() in [ext]:
            raise exceptions.ValidationError(
                "El archivo no tiene el formato correcto."
            )

        filename = fs.save(invoice_file.name, invoice_file)
        uploaded_file_url = fs.url(filename)
        return f"{BASE_URL}/{uploaded_file_url}"

    def save(self):
        with MongoDBHandler('purchase_orders') as db:
            required_fields = ['supplier_id', 'home_production_id',
                               'request_by', 'created', 'items', 'subtotal', 'iva', 'total']
            if all(i in self.data for i in required_fields):
                home_production = self.__check_home_production(
                    db, self.data['home_production_id'])
                supplier = self.__check_supplier(db, self.data['supplier_id'])
                if supplier:
                    data = self.data
                    data['project'] = f"{home_production['front']} - OD {home_production['od']}" if data['type'] == 'OD' else 'Sin proyecto'
                    data['folio'] = db.set_next_folio('purchase_order')
                    data['invoiced_status'] = 0
                    data['delivered_status'] = 0
                    id = db.insert(data)
                    if data['status'] == 1:
                        send_notification(get_message(
                            'purchase_order_generated', f'Nueva orden de compra generada: {data['project']}'))
                    return created({'id': str(id)})
                return bad_request('El proveedor seleccionado no existe.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('purchase_orders') as db:
            filters = {}
            if self.supplier:
                filters['supplier_id'] = self.supplier
            if self.status:
                filters['status'] = int(
                    self.status) if self.status.isdigit() else self.status
                if self.status == 'processed':
                    filters['status'] = {"$gt": 1}
            if self.q:
                filters['$or'] = [
                    {'project': {'$regex': self.q, '$options': 'i'}},
                    {'subject': {'$regex': self.q, '$options': 'i'}},
                    {'request_by_name': {'$regex': self.q, '$options': 'i'}},
                    {'approved_by_name': {'$regex': self.q, '$options': 'i'}},
                ]
            if self.supplier:
                filters['supplier_id'] = self.supplier
            if self.project:
                filters['home_production_id'] = self.project
            purchase_orders = db.extract(filters)
            paginator = Paginator(purchase_orders, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                PurchaseOrderSerializer(page.object_list, many=True).data
            )

    def get_by_id(self):
        with MongoDBHandler('purchase_orders') as db:
            purchase_order = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if purchase_order:
                hp = self.__check_home_production(
                    db, purchase_order[0]['home_production_id'])
                purchase_order[0]['selected_rows'] = [item['id']
                                                      for item in purchase_order[0]['items']]
                purchase_order[0]['lots'] = hp['lots']['prototypes'] if hp else {}
                return ok(PurchaseOrderSerializer(purchase_order[0]).data)
            return not_found('Orden de compra no encontrada.')

    def get_projects(self):
        with MongoDBHandler('home_production') as db:
            projects = [{
                'home_production_id': None,
                'name': 'Sin proyecto',
                'od': None,
                'front': None,
                'lots': {}
            }]
            home_production = db.extract()
            if home_production:
                for hp in home_production:
                    projects.append({
                        'home_production_id': str(hp['_id']),
                        'name': f"{hp['front']} - OD {hp['od']}",
                        'od': hp['od'],
                        'front': hp['front'],
                        'lots': hp['lots']['prototypes'] if 'prototypes' in hp['lots'] else {}
                    })
            return ok(projects)

    def get_suppliers(self):
        with MongoDBHandler('explosion') as db:
            suppliers = []
            if self.type_project == 'SP':
                suppliers = SupplierSerializer(
                    MongoDBHandler.find(db, 'suppliers', {}, 'name'), many=True).data
            else:
                viewed = set()
                materials = db.extract(
                    {'home_production_id': self.home_production_id})
                for material in materials:
                    supplier = self.__check_supplier(
                        db, material['supplier_id'])
                    if supplier:
                        supplier_id = str(supplier['_id'])
                        if supplier_id not in viewed:
                            suppliers.append({
                                '_id': supplier_id,
                                'name': supplier['name']
                            })
                            viewed.add(supplier_id)
            return ok({'suppliers_list': suppliers, 'last_consecutive': db.get_next_folio('purchase_order')})

    def get_materials(self):
        with MongoDBHandler('explosion') as db:
            data = []
            costs = {}
            items = db.extract(
                {'home_production_id': self.home_production_id, 'supplier_id': self.supplier_id})
            for i, item in enumerate(items):
                material = self.__process_material(db, item)
                if item and material:
                    data.append({
                        'id': i,
                        'supplier_id': item['supplier_id'],
                        'required': item['gran_total'],
                        'quantities': item['explosion'],
                        'color': item.get('color', None),
                        'source': 'volumetry',
                        **material,
                    })
            materials = self.__check_materials(db, data)
            if len(materials) > 0:
                subtotal = sum(item['total'] for item in materials)
                costs = {
                    'subtotal': subtotal,
                    'iva': round(subtotal*.16, 2),
                    'total': round(subtotal*1.16, 2),
                }
            else:
                costs = {
                    'subtotal': 0,
                    'iva': 0,
                    'total': 0,
                }

            return ok({'costs': costs, 'items': materials})

    def update(self):
        with MongoDBHandler('purchase_orders') as db:
            purchase_order = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            required_fields = ['supplier_id', 'home_production_id',
                               'request_by', 'created', 'items', 'subtotal', 'iva', 'total']
            if purchase_order:
                if all(i in self.data for i in required_fields):
                    home_production = self.__check_home_production(
                        db, self.data['home_production_id'])
                    supplier = self.__check_supplier(
                        db, self.data['supplier_id'])
                    if supplier:
                        data = self.data
                        if isinstance(home_production, dict) and data['type'] == 'OD':
                            data['project'] = f"{home_production['front']} - OD {home_production['od']}"
                        else:
                            data['project'] = 'Sin proyecto'
                        db.update({'_id': ObjectId(self.id)}, data)
                        message_status = 'guardada' if data['status'] == 0 else 'generada'
                        return ok(f'Orden de compra {message_status} correctamente.')
                    return bad_request('El proveedor seleccionado no existe.')
                return bad_request('Algunos campos requeridos no han sido completados.')
            return not_found('La orden de compra no existe.')

    def modify(self):
        with MongoDBHandler('purchase_orders') as db:
            purchase_order = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if purchase_order:
                if self.data['status'] == 2:
                    data = self.__prepare_data_files(
                        db, PurchaseOrderSerializer(purchase_order[0]).data)
                    self.data['excel_file'] = f"{settings.BASE_URL}/{create_xlsx(data)}"
                    pdf = generate_pdf({
                        'purchase_order_id': str(data['_id']),
                        'client': data['client'],
                        'number': data['number'],
                        'supplier': data['supplier'],
                        'company': data['company'],
                        'date': data['created'],
                        'location': data['location'],
                        'division': data['division'],
                        'materials': data['materials'],
                        'subtotal': data['subtotal'],
                        'total': data['total'],
                        'payment_method': data.get('payment_method', ''),
                        'payment_form': data.get('payment_form', ''),
                        'cfdi': data.get('cfdi', ''),
                        'invoice_email': data.get('invoice_email', ''),
                        'notes': data.get('subject', '')
                    })
                    self.data['pdf_file'] = f"{settings.BASE_URL}/{pdf}"
                db.update({'_id': ObjectId(self.id)}, self.data)
                message_status = 'aprobada' if self.data['status'] == 2 else 'rechazada'
                return ok(f'Orden de compra {message_status} correctamente.')
            return not_found('La orden de compra no existe.')

    def delete(self):
        with MongoDBHandler('purchase_orders') as db:
            purchase_order = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if purchase_order:
                db.delete({'_id': ObjectId(self.id)})
                return ok('Orden de compra eliminada correctamente.')
            return not_found('La orden de compra no existe.')

    def input_register(self):
        with MongoDBHandler('purchase_orders') as db:
            purchase_order = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if purchase_order:
                if 'items' in self.data:
                    _ = [item["delivered"].update(
                        {"registration_date": datetime.now().isoformat()}) for item in self.data['items']]
                    self.data['delivered_status'] = InboundUseCase.check_quantities(
                        self.data['items'])
                    db.update({'_id': ObjectId(self.id)}, self.data)
                    fields = ["color", "source", "material_id", "concept", "measurement", "supplier_id", "supplier_code",
                              "inventory_price", "market_price", "sku", "presentation", "reference", "delivered", "total_quantity", "division"]
                    items = [{k: d[k] for k in fields if k in d}
                             for d in self.data['items']]
                    InboundUseCase.register(
                        purchase_order_id=self.id,
                        supplier_id=purchase_order[0]['supplier_id'],
                        project={
                            'id': str(purchase_order[0]['_id']),
                            'name': purchase_order[0]['project'],
                            'type': 'OD' if purchase_order[0]['home_production_id'] else 'Proyecto Especial'
                        },
                        items=items,
                        folio=db.set_next_folio('purchase_order'),
                        notes=self.data['notes'] if 'notes' in self.data and self.data['notes'] else None
                    )
                    return ok('Registro de entrada de materiales guardado correctamente')
                return bad_request('Algunos campos requeridos no han sido completados.')
            return not_found('La orden de compra no existe.')

    def upload_invoice(self):
        with MongoDBHandler('purchase_orders') as db:
            purchase_order = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if purchase_order:
                serializer = InvoiceUploadSerializer(data=self.data)
                data = dict(self.data.items())
                if serializer.is_valid():
                    try:
                        db.update({'_id': ObjectId(self.id)}, {
                            'paid': data['paid'] == 'true',
                            'invoiced_status': 2 if data['paid'] == 'true' else 1,
                            'invoice_pdf_file': self.__upload_file(data['pdf_file'], 'pdf'),
                            'invoice_xml_file': self.__upload_file(data['xml_file'], 'xml'),
                        })
                        return ok('Los archivos de la factura se han cargado correctamente.')
                    except Exception as e:
                        return bad_request(f'Error: {str(e)}, "Trace": {traceback.format_exc()}')
                elif 'paid' in data:
                    db.update({'_id': ObjectId(self.id)}, {
                        'paid': data['paid'] == 'true',
                        'invoiced_status': 2 if data['paid'] == 'true' else 1,
                    })
                    return ok('Los cambios en la factura se han guardado correctamente.')
                else:
                    return bad_request(serializer.errors)
            return not_found('La orden de compra no existe.')
