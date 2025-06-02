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
                            'explosion': amounts,
                            'gran_total': gran_total
                        })

    def get(self):
        with MongoDBHandler('explosion') as db:
            explosion = db.extract(
                {'home_production_id': self.home_production_id})
            if explosion:
                return ok(ExplosionSerializer(explosion, many=True).data)
            return not_found('No exite explosión de materiales para la OD seleccionada.')
