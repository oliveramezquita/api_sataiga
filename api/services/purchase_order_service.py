from rest_framework.exceptions import ValidationError

from api.repositories.purchase_order_repository import PurchaseOrderRepository
from api.repositories.explosion_repository import ExplosionRepository
from api.repositories.concept_repository import ConceptRepository


class PurchaseOrderService:
    def __init__(self, purchase_order_id: str):
        self.purchase_order_id = purchase_order_id
        self.purchase_order_repository = PurchaseOrderRepository()
        self.explosion_repository = ExplosionRepository()
        self.concept_repository = ConceptRepository()
        self.project_id, self.supplier_id, self.type, self.ps_materials = self._get_purchase_data()

    def _get_purchase_data(self) -> tuple:
        purchase_order = self.purchase_order_repository.find_by_id(
            self.purchase_order_id
        )

        if not purchase_order:
            return []

        project_id = purchase_order.get('project_id')
        supplier_id = purchase_order.get('supplier_id')
        purchase_type = purchase_order.get('type', 'SP')
        items = purchase_order.get('items', [])
        materials = {
            item['material_id']: {
                'concept': item['concept'],
                'total_quantity': float(item['total_quantity'])
            }
            for item in items
        }

        return project_id, supplier_id, purchase_type, materials

    @staticmethod
    def group_materials(materials, supplier_id):
        grouped = {}

        for material in materials:
            # Filtrar por proveedor
            if material['supplier_id'] != supplier_id:
                continue

            material_id = material['id']

            if material_id not in grouped:
                grouped[material_id] = material.copy()
            else:
                grouped[material_id]['amount'] += material['amount']

        return list(grouped.values())

    def check_purchased_materials(self):
        material_ids = list(self.ps_materials.keys())

        if self.type == 'VS':
            explosion = self.explosion_repository.find_by_ids(
                ids=material_ids,
                key='material_id'
            )

            exp_materials = {
                item['material_id']: {
                    'gran_total': item['gran_total'],
                    'purchased': item.get('purchased', 0)
                }
                for item in explosion
            }

            for material_id, material in self.ps_materials.items():
                exp_material = exp_materials.get(material_id)

                if not exp_material:
                    raise ValidationError(
                        f"El material '{material['concept']}' no se encontró en la explosión de materiales."
                    )

                total = material['total_quantity'] + exp_material['purchased']

                if total > exp_material['gran_total']:
                    raise ValidationError(
                        f"El material '{material['concept']}' excede la cantidad requerida en la orden de compra. "
                        f"Requerido: {exp_material['gran_total']}, "
                        f"comprado: {exp_material['purchased']}, "
                        f"solicitado: {material['total_quantity']}."
                    )

        elif self.type == 'PE':
            concepts = self.concept_repository.find_all(
                {'project_id': self.project_id})

            items = []
            for concept in concepts:
                materials = (
                    concept.get('materials') or {}
                ).get('items') or []

                items.extend(materials)

            grouped = PurchaseOrderService.group_materials(
                items,
                self.supplier_id
            )

            concept_materials = {
                item['id']: {
                    'gran_total': item['amount'],
                    'purchased': item.get('purchased', 0)
                }
                for item in grouped
            }

            for material_id, material in self.ps_materials.items():
                concept_material = concept_materials.get(material_id)

                if not concept_material:
                    raise ValidationError(
                        f"El material '{material['concept']}' no se encontró en la explosión de materiales."
                    )

                total = material['total_quantity'] + \
                    concept_material['purchased']

                if total > concept_material['gran_total']:
                    raise ValidationError(
                        f"El material '{material['concept']}' excede la cantidad requerida en la orden de compra. "
                        f"Requerido: {concept_material['gran_total']}, "
                        f"comprado: {concept_material['purchased']}, "
                        f"solicitado: {material['total_quantity']}."
                    )

        return True

    def set_purchased_materials(self):
        material_ids = list(self.ps_materials.keys())

        if self.type == 'VS':
            explosion = self.explosion_repository.find_by_ids(
                ids=material_ids,
                key='material_id'
            )

            exp_materials = {
                item['material_id']: {
                    'gran_total': item['gran_total'],
                    'purchased': item.get('purchased', 0)
                }
                for item in explosion
            }

            for material_id, material in self.ps_materials.items():
                exp_material = exp_materials.get(material_id)

                if not exp_material:
                    raise ValidationError(
                        f"El material '{material['concept']}' no se encontró en la explosión de materiales."
                    )

                total = material['total_quantity'] + exp_material['purchased']
                data = {'purchased': total}
                if total == exp_material['gran_total']:
                    data['status'] = 1

                self.explosion_repository.update_one(
                    {'material_id': material_id}, data)

            return True

        if self.type == 'PE':
            return True
