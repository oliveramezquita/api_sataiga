import json
from django.http import HttpResponse
from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE
from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from pymongo import errors
from api.helpers.http_responses import created, bad_request, ok_paginated, ok
from django.core.paginator import Paginator
from api.serializers.section_serializer import SectionSerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation


class SectionUseCase:
    def __init__(self, request=None, **kwargs):
        if request:
            params = parse_qs(request.META['QUERY_STRING'])
            self.page = params['page'][0] if 'page' in params else 1
            self.page_size = params['itemsPerPage'][0] \
                if 'itemsPerPage' in params else DEFAULT_PAGE_SIZE
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)

    def save(self):
        with MongoDBHandler('sections') as db:
            required_fields = ['parent', 'value']
            if all(i in self.data for i in required_fields):
                try:
                    db.create_unique_index('value')
                    db.insert(self.data)
                    return created('Sección creada correctamente.')
                except errors.DuplicateKeyError:
                    return bad_request('El nombre de la sección proporcionado ya ha sido registrado. Por favor, utilice un nombre diferente.')
            return bad_request('Algunos campos requeridos no han sido completados.')

    def get(self):
        with MongoDBHandler('sections') as db:
            sections = db.extract()
            paginator = Paginator(sections, per_page=self.page_size)
            page = paginator.get_page(self.page)
            return ok_paginated(
                paginator,
                page,
                SectionSerializer(page.object_list, many=True).data
            )

    def update(self):
        with MongoDBHandler('sections') as db:
            section = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if section:
                db.update({'_id': ObjectId(self.id)}, self.data)
                return ok('Sección actualizada correctamente.')
            return bad_request('La sección no existe')

    def tree_view(self):
        with MongoDBHandler('sections') as db:
            sections = db.extract()

            tree_sections = {}
            for section in sections:
                if section['parent'] not in ['Historial', 'Logs']:
                    if section['parent'] not in tree_sections:
                        tree_sections[section['parent']] = []
                    tree_sections[section['parent']].append({
                        '_id': str(section['_id']),
                        'name': self.__set_name_section(section),
                        'value': section['value'],
                    })

            return HttpResponse(json.dumps(tree_sections), content_type='application/json')

    def __set_name_section(self, section):
        name = section['parent']
        if 'level_1' in section:
            name = section['level_1']
        if 'level_2' in section:
            name = f'{name} - {section['level_2']}'
        return name
