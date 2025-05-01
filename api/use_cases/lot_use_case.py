from api_sataiga.handlers.mongodb_handler import MongoDBHandler
from api.helpers.http_responses import bad_request, ok, not_found
from api.serializers.lot_serializer import LotSerializer
from bson import ObjectId
from api.helpers.validations import objectid_validation
from collections import Counter
from api.use_cases.explosion_use_case import ExplosionUseCase


class LotUseCase:
    def __init__(self, request=None, **kwargs):
        self.data = kwargs.get('data', None)
        self.id = kwargs.get('id', None)
        self.home_production_id = kwargs.get('home_production_id', None)

    def __update_hp_lots(self, db, home_production_id):
        lots = db.extract({'home_production_id': home_production_id})
        if lots:
            status_map = {
                0: 'Pendiente',
                1: 'En Progreso',
                2: 'Finalizado'
            }

            prototype_counter = Counter()
            status_counter = Counter()

            for item in lots:
                prototype_counter[item['prototype']] += 1
                status_counter[status_map[item['status']]] += 1

            result = {
                'total': len(lots),
                'prototypes': dict(prototype_counter),
                'status': dict(status_counter)
            }

            status = 0
            if 'Pendiente' in result['status'] and result['status']['Pendiente'] == len(lots):
                status = 0
            elif 'En Progreso' in result['status'] and result['status']['En Progreso'] > 0:
                status = 1
            elif 'Finalizado' in result['status'] and result['status']['Finalizado'] == len(lots):
                status = 2

            progress = 0
            if 'Finalizado' in result['status'] and result['status']['Finalizado'] > 0:
                progress = (result['status']['Finalizado'] / len(lots)) * 100

            MongoDBHandler.modify(db, 'home_production', {'_id': ObjectId(home_production_id)}, {
                'lots': result,
                'progress': int(progress),
                'status': status,
            })

    def __update_explosion(self):
        explosion_use_case = ExplosionUseCase(
            home_production_id=self.home_production_id)
        explosion_use_case.create()

    def save(self):
        with MongoDBHandler('lots') as db:
            errors = []
            lots = []
            if 'lots' in self.data and len(self.data['lots']) > 0:
                currentLots = db.extract(
                    {'home_production_id': self.home_production_id})
                if currentLots:
                    db.delete(
                        {'home_production_id': self.home_production_id})

                required_fields = ['prototype', 'block', 'lot', 'laid']
                for lot in self.data['lots']:
                    if all(i in lot for i in required_fields):
                        status = lot['status'] if 'status' in lot else 0
                        db.insert({
                            'home_production_id': self.home_production_id,
                            **lot,
                            'status': status,
                        })
                        lots = db.extract(
                            {'home_production_id': self.home_production_id})
                    else:
                        errors.append(lot)
                self.__update_hp_lots(db, self.home_production_id)
                self.__update_explosion()
                return ok({
                    'success': LotSerializer(lots, many=True).data,
                    'errors': errors,
                })
            return bad_request('No existen lotes o el id de la OD en los campos añadidos.')

    def get(self):
        with MongoDBHandler('lots') as db:
            lots = db.extract({'home_production_id': self.home_production_id})
            if lots:
                return ok(LotSerializer(lots, many=True).data)
            return ok([])

    def update(self):
        with MongoDBHandler('lots') as db:
            lot = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if lot:
                db.update({'_id': ObjectId(self.id)}, self.data)
                self.__update_hp_lots(db, lot[0]['home_production_id'])
                return ok('Lote actualizado correctamente.')
            return not_found('El lote no existe.')

    def delete(self):
        with MongoDBHandler('lots') as db:
            lot = db.extract(
                {'_id': ObjectId(self.id)}) if objectid_validation(self.id) else None
            if lot:
                db.delete({'_id': ObjectId(self.id)})
                self.__update_hp_lots(db, lot[0]['home_production_id'])
                return ok('Lote eliminado correctamente.')
            return not_found('El lote no existe.')
