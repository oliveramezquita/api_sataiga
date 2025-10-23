from api.repositories.template_repository import TemplateRepository
from api.repositories.client_repository import ClientRepository
from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Any, Optional


class TemplateNotFoundError(Exception):
    pass


class TemplateService:
    """Lógica de negocio pura para Templates."""

    def __init__(self):
        self.template_repo = TemplateRepository()
        self.client_repo = ClientRepository()

    def _validate_fields(self, data: dict, required_fields: list[str]):
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise ValueError(
                f'Campos requeridos faltantes: {", ".join(missing)}')

    def _validate_field_name(self, element: str) -> None:
        """
        Evita nombres de campo peligrosos para Mongo: ni vacíos, ni con '.' ni con '$'.
        """
        if not element or not isinstance(element, str):
            raise ValueError(
                "El nombre de 'element' es obligatorio y debe ser str no vacío.")
        if "." in element or "$" in element:
            raise ValueError(
                "El nombre de 'element' no puede contener '.' ni '$'.")

    def create(self, data: dict) -> str:
        self._validate_fields(data, ['name'])
        if 'client_id' in data:
            client = self.client_repo.find_valid_client(data['client_id'])
            if not client:
                raise LookupError(
                    'El cliente seleccionado no existe o no es válido.')
        _ = self.template_repo.insert(data)
        return data['name']

    def get_all(self, client_id: str = None):
        filters = {}

        if client_id:
            filters["$or"] = [
                {"client_id": client_id},
                {"client_id": None}
            ]
        return self.template_repo.find_all(query=filters, order_field='created_at', order=-1)

    def get_by_id(self, template_id: str):
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise LookupError('La plantilla no existe.')
        return template

    def update(self, template_id: str, data: dict):
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise LookupError('La plantilla no existe.')
        self.template_repo.update(template_id, data)

    def delete(self, template_id: str):
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise LookupError('La plantilla no existe.')
        self.template_repo.delete(template_id)

    def process_items(self, template_id: str, element: str, item: Mapping[str, Any]) -> None:
        """
        Agrega o actualiza un item dentro de template[element].items.
        Si el item ya existe (por _id), actualiza su cantidad y total.
        Luego recalcula todos los subtotales globales (sumando todos los elementos).

        Cada elemento (materials, labor, indirects, etc.) tiene esta estructura:
        {
            "items": [ { "id": ..., "total": ... }, ... ],
            "total": <float>
        }

        El documento global quedará así:
        {
            "materials": {...},
            "labor": {...},
            "subtotal": <float>,
            "iva": <float>,
            "total": <float>
        }
        """
        self._validate_field_name(element)

        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(
                f"No existe el template: {template_id}")

        if not item or "total" not in item or "id" not in item:
            raise ValueError("`item` debe incluir las claves 'id' y 'total'.")

        # 🔧 Asegura estructura base
        element_value: Optional[Any] = template.get(element)
        if not isinstance(element_value, dict):
            element_value = {"items": [], "total": 0}
            template[element] = element_value

        items = element_value.get("items", [])
        existing_item = next(
            (i for i in items if i["id"] == item["id"]), None)

        if existing_item:
            # 🔁 Actualiza cantidad o total del item existente
            existing_item.update(item)
        else:
            # ➕ Agrega nuevo item
            items.append(dict(item))

        # 🧮 Recalcula el total del elemento
        element_total = sum(Decimal(str(i["total"])) for i in items)
        element_value["total"] = float(element_total.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP))
        template[element] = element_value

        # 🧮 Calcula subtotal sumando todos los elementos tipo dict que tengan "total"
        subtotal = Decimal("0.00")
        for key, value in template.items():
            if isinstance(value, dict) and "total" in value:
                subtotal += Decimal(str(value["total"]))

        subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva = (subtotal * Decimal("0.16")
               ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (subtotal + iva).quantize(Decimal("0.01"),
                                          rounding=ROUND_HALF_UP)

        # ✅ Actualiza los campos globales
        template["subtotal"] = float(subtotal)
        template["iva"] = float(iva)
        template["total"] = float(total)

        # 💾 Persistir en Mongo
        update = {
            element: element_value,
            "subtotal": float(subtotal),
            "iva": float(iva),
            "total": float(total),
        }

        self.template_repo.update(template_id, update)

    def delete_item(self, template_id: str, element: str, item_id: str) -> None:
        """
        Elimina un item dentro de template[element].items según su _id.
        Luego recalcula el total del elemento, subtotal, IVA y total global.

        Estructura esperada:
        {
            "materials": { "items": [ {"id": "...", "total": ...}, ... ], "total": ... },
            "subtotal": ...,
            "iva": ...,
            "total": ...
        }
        """
        self._validate_field_name(element)

        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(
                f"No existe la plantilla: {template_id}")

        element_value: Optional[Any] = template.get(element)
        if not isinstance(element_value, dict) or "items" not in element_value:
            raise ValueError(
                f"El elemento '{element}' no tiene estructura válida en la plantilla.")

        items = element_value.get("items", [])
        new_items = [i for i in items if str(i.get("id")) != str(item_id)]

        # 🧮 Recalcular total del elemento
        if new_items:
            element_total = sum(Decimal(str(i["total"])) for i in new_items)
            element_value["items"] = new_items
            element_value["total"] = float(element_total.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP))
        else:
            # Si ya no quedan items, resetear el bloque del elemento
            element_value = {"items": [], "total": 0.0}

        template[element] = element_value

        # 🧮 Recalcula subtotal global sumando todos los elementos tipo dict con "total"
        subtotal = Decimal("0.00")
        for key, value in template.items():
            if isinstance(value, dict) and "total" in value:
                subtotal += Decimal(str(value["total"]))

        subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva = (subtotal * Decimal("0.16")
               ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (subtotal + iva).quantize(Decimal("0.01"),
                                          rounding=ROUND_HALF_UP)

        # ✅ Actualizar campos globales
        template["subtotal"] = float(subtotal)
        template["iva"] = float(iva)
        template["total"] = float(total)

        # 💾 Guardar en Mongo
        update = {
            element: element_value,
            "subtotal": float(subtotal),
            "iva": float(iva),
            "total": float(total),
        }

        self.template_repo.update(template_id, update)

    def process_indirect_costs(self, template_id: str, indirect_costs: str) -> None:
        """
        Agrega o actualiza los costos indirectos a un Template y recalcula subtotal, IVA y total.
        El subtotal base se obtiene dinámicamente de la suma de production, equipment y materials.
        """

        # 🔹 Obtener el template
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(
                f"No existe la plantilla: {template_id}")

        # 🔹 Conversión segura a Decimal
        try:
            indirect = Decimal(str(indirect_costs or 0))
        except Exception:
            raise ValueError(f"Valor de indirectos inválido: {indirect_costs}")

        # 🔹 Obtener los totales base
        production_total = Decimal(
            str(template.get("production", {}).get("total", 0)))
        equipment_total = Decimal(
            str(template.get("equipment", {}).get("total", 0)))
        materials_total = Decimal(
            str(template.get("materials", {}).get("total", 0)))

        # 🔹 Calcular subtotal base sin indirectos
        subtotal_base = (production_total + equipment_total + materials_total).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 🔹 Calcular valor del indirecto sobre el subtotal base
        indirect_value = (subtotal_base * indirect / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 🔹 Nuevo subtotal con indirecto aplicado
        new_subtotal = (subtotal_base + indirect_value).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 🔹 IVA (16%)
        iva = (new_subtotal * Decimal("0.16")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 🔹 Total final
        total = (new_subtotal + iva).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 🔹 Actualizar datos
        update_data = {
            "indirect": float(indirect),
            "subtotal": float(new_subtotal),
            "iva": float(iva),
            "total": float(total),
        }

        self.template_repo.update(template_id, update_data)

    def clear_indirect_costs(self, template_id: str) -> None:
        """
        Limpia los costos indirectos de un Template y recalcula subtotal, IVA y total
        con base en los totales de production, equipment y materials.
        """

        # 🔹 Obtener el template
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(
                f"No existe la plantilla: {template_id}")

        # 🔹 Obtener totales base de cada sección
        production_total = Decimal(
            str(template.get("production", {}).get("total", 0) or 0))
        equipment_total = Decimal(
            str(template.get("equipment", {}).get("total", 0) or 0))
        materials_total = Decimal(
            str(template.get("materials", {}).get("total", 0) or 0))

        # 🔹 Calcular subtotal base sin indirectos
        subtotal_base = (production_total + equipment_total + materials_total).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 🔹 Calcular IVA (16%)
        iva = (subtotal_base * Decimal("0.16")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 🔹 Calcular total final
        total = (subtotal_base + iva).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # 🔹 Actualizar datos
        update_data = {
            "indirect": None,             # 🔸 Lo dejamos explícitamente nulo
            "subtotal": float(subtotal_base),
            "iva": float(iva),
            "total": float(total),
        }

        self.template_repo.update(template_id, update_data)
