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

    def __get_volumetry(self, db, client_id, front):
        volumetries = MongoDBHandler.find(
            db, 'volumetries', {'client_id': client_id, 'front': front})
        if volumetries:
            return volumetries
        return None

    # TODO: Hacer de esta funcion un helper
    def __to_float(self, val, default=0.0):
        try:
            if val is None:
                return default
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                s = val.strip()
                if not s:
                    return default
                # Opcional: quitar separadores de miles
                s = s.replace(',', '')
                return float(s)
        except (TypeError, ValueError):
            return default
        return default

    def __total_from_prototypes(self, prototypes: list[dict]) -> float:
        """Suma factory + instalation de todos los prototypes."""
        total = 0.0
        for p in prototypes:
            q = p.get('quantities', {})
            total += self.__to_float(q.get('factory')) + \
                self.__to_float(q.get('instalation'))
        return round(total, 2)

    def __remove_prototype(self, area: dict, prototype: str):
        area["prototypes"] = [p for p in area.get("prototypes", [])
                              if p.get("prototype") != prototype]
        area["total"] = self.__total_from_prototypes(area["prototypes"])
        return area

    def __update_by_area(self, explosion: list[dict], area_name: str, new_entry: dict) -> list[dict]:
        for i, d in enumerate(explosion):
            if d.get("area") == area_name:
                explosion[i] = new_entry
                break
        return explosion

    def __takeout_amounts(self, db, item, hp):
        lots_prototypes = hp['lots']['prototypes']

        explosion_docs = db.find(db, 'explosion', {
            'home_production_id': str(hp['_id']),
            'material_id': item['material_id'],
            'supplier_id': item['supplier_id'],
        })

        # Si el prototype no está contemplado en lots, no hay nada que mover
        if item['prototype'] not in lots_prototypes:
            return explosion_docs[0]['explosion'] if explosion_docs else []

        multiplier = float(lots_prototypes[item['prototype']])

        def scaled(v):
            f = round(self.__to_float(v.get('factory')) * multiplier, 2)
            ins = round(self.__to_float(v.get('instalation')) * multiplier, 2)
            return f, ins

        # ---- Caso SIN documento previo de explosion ----
        if not explosion_docs:
            amounts = []
            for v in item['volumetry']:
                factory, instalation = scaled(v)
                if factory > 0 or instalation > 0:
                    prototypes = [{
                        'prototype': item['prototype'],
                        'quantities': {
                            'factory': factory,
                            'instalation': instalation,
                        }
                    }]
                    amounts.append({
                        'area': v['area'],
                        'prototypes': prototypes,
                        # factory + instalation
                        'total': self.__total_from_prototypes(prototypes),
                    })
            return amounts

        # ---- Caso CON documento previo de explosion ----
        areas = explosion_docs[0]['explosion']

        for v in item['volumetry']:
            factory, instalation = scaled(v)
            exp = next((d for d in areas if d.get("area") == v['area']), None)

            if exp:
                # 1) Quitar si existía ese prototype
                exp = self.__remove_prototype(exp, item['prototype'])

                # 2) Agregarlo si hay valores
                if factory > 0 or instalation > 0:
                    exp['prototypes'].append({
                        'prototype': item['prototype'],
                        'quantities': {
                            'factory': factory,
                            'instalation': instalation,
                        }
                    })

                # 3) Recalcular total como factory + instalation
                exp['total'] = self.__total_from_prototypes(exp['prototypes'])

                # 4) Persistir en la lista de áreas
                areas = self.__update_by_area(areas, v['area'], exp)

            else:
                # No existía el área: crearla si aporta valores
                if factory > 0 or instalation > 0:
                    prototypes = [{
                        'prototype': item['prototype'],
                        'quantities': {
                            'factory': factory,
                            'instalation': instalation,
                        }
                    }]
                    areas.append({
                        'area': v['area'],
                        'prototypes': prototypes,
                        'total': self.__total_from_prototypes(prototypes),
                    })

        return areas

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
                    db, home_production['client_id'], home_production['front'])
                for volumetry in volumetries:
                    amounts = self.__takeout_amounts(
                        db, volumetry, home_production)
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
