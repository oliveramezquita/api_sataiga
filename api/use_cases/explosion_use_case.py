from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from bson import ObjectId
from api.helpers.validations import objectid_validation
from api.helpers.http_responses import not_found, ok
from api.serializers.explosion_serializer import ExplosionSerializer


class ExplosionUseCase:
    def __init__(self, request=None, **kwargs):
        self.home_production_id = kwargs.get('home_production_id', None)

    def __get_home_production(self, db):
        home_production = MongoDBHandler.find(db, 'home_production', {'_id': ObjectId(
            self.home_production_id)}) if objectid_validation(self.home_production_id) else None
        if home_production:
            return home_production[0]
        return None

    def __get_home_production_by_data(self, db, client_id, front):
        home_production = MongoDBHandler.find(db, 'home_production', {
            'client_id': client_id,
            'front': front
        })
        if home_production:
            return home_production[0]
        return None

    def __get_volumetry(self, db, front):
        volumetries = MongoDBHandler.find(db, 'volumetries', {'front': front})
        if volumetries:
            return volumetries
        return None

    def __takeout_amounts(self, volumetry, lots_prototypes):
        amounts = []
        for v in volumetry:
            prototypes = []
            total = 0
            for p in v['prototypes']:
                if p['prototype'] in lots_prototypes:
                    factory = float(p['quantities']['factory']) * \
                        float(lots_prototypes[p['prototype']])
                    instalation = float(
                        p['quantities']['instalation']) * float(lots_prototypes[p['prototype']])
                    amount = factory + instalation
                    if amount > 0:
                        prototypes.append({
                            'prototype': p['prototype'],
                            'quantities': {
                                'factory': round(factory, 2),
                                'instalation':  round(instalation, 2),
                            }
                        })
                        total += amount
            if total > 0:
                amounts.append({
                    'area': v['area'],
                    'prototypes': prototypes,
                    'total': round(total, 2),
                })
        return amounts

    def __assign_color(self, db, **kwargs):
        data = MongoDBHandler.find(db, 'quantification', {
            'prototype': kwargs.get('prototype', None),
            'front': kwargs.get('front', None),
            'client_id': kwargs.get('client_id', None),
        })
        if data:
            results = []
            seen = set()

            for item in data:
                quantification = item.get('quantification', {})
                for _, materials in quantification.items():
                    for material_item in materials:
                        material = material_item.get('material', {})
                        color = material.get('color')
                        material_id = material_item.get('id')

                        if color and material_id:
                            key = (material_id, color)
                            if key not in seen:
                                results.append(
                                    {'id': material_id, 'color': color})
                                seen.add(key)

            for material in results:
                MongoDBHandler.modify(
                    db,
                    'explosion',
                    {
                        'home_production_id': kwargs.get('home_production_id', None),
                        'material_id': material['id'],
                    },
                    {'color': material['color'], }
                )

    def create(self):
        with MongoDBHandler('explosion') as db:
            home_production = self.__get_home_production(db)
            if home_production:
                volumetries = self.__get_volumetry(
                    db, home_production['front'])
                for volumetry in volumetries:
                    amounts = self.__takeout_amounts(
                        volumetry['volumetry'],
                        home_production['lots']['prototypes'])
                    gran_total = sum(item["total"] for item in amounts)
                    explosion = db.extract({
                        'home_production_id': self.home_production_id,
                        'material_id': volumetry['material_id']
                    })
                    if explosion:
                        db.update({'_id': ObjectId(explosion[0]['_id'])}, {
                            'explosion': amounts,
                            'gran_total': gran_total
                        })
                    else:
                        db.insert({
                            'home_production_id': self.home_production_id,
                            'material_id': volumetry['material_id'],
                            'supplier_id': volumetry['supplier_id'],
                            'explosion': amounts,
                            'gran_total': gran_total
                        })
                for prototype in home_production['lots']['prototypes'].keys():
                    self.__assign_color(
                        db,
                        prototype=prototype,
                        front=home_production['front'],
                        client_id=home_production['client_id'],
                        home_production_id=self.home_production_id,
                    )

    def get(self):
        with MongoDBHandler('explosion') as db:
            explosion = db.extract(
                {'home_production_id': self.home_production_id})
            if explosion:
                return ok(ExplosionSerializer(explosion, many=True).data)
            return not_found('No exite explosión de materiales para la OD seleccionada.')
