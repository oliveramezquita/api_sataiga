from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Mapping, Any, List
from zipfile import BadZipFile
from bson import ObjectId

from openpyxl import load_workbook, Workbook
from rest_framework.exceptions import ValidationError
from openpyxl.utils.exceptions import InvalidFileException

from api.repositories.project_repository import ProjectRepository
from api.repositories.concept_repository import ConceptRepository
from api.repositories.template_repository import TemplateRepository
from api.repositories.material_repository import MaterialRepository
from api.tasks.project_tasks import recalculate_project_totals


class ConceptNotFoundError(Exception):
    pass


class ConceptService:
    """Lógica de negocio pura para Conceptos."""

    ELEMENT_PATHS: List[List[str]] = [
        ["materials"],
        ["production"],
        ["equipment"],
        ["installation"],
        ["prov", "materials"],
        ["prov", "equipment"],
        ["prov", "mo"],
    ]

    def __init__(self):
        self.project_repo = ProjectRepository()
        self.concept_repo = ConceptRepository()
        self.template_repo = TemplateRepository()
        self.material_repo = MaterialRepository()

    # ────────────────────────────────────────────────────────────────────────────────
    # VALIDACIONES Y UTILIDADES BÁSICAS
    # ────────────────────────────────────────────────────────────────────────────────
    def _validate_fields(self, data: dict, required_fields: list[str]):
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise ValueError(
                f'Campos requeridos faltantes: {", ".join(missing)}')

    def _validate_field_name(self, element: str) -> None:
        """Evita nombres peligrosos para Mongo."""
        if not element or not isinstance(element, str):
            raise ValueError(
                "El nombre de 'element' es obligatorio y debe ser str no vacío.")
        if "." in element or "$" in element:
            raise ValueError(
                "El nombre de 'element' no puede contener '.' ni '$'.")

    def _get_path_dict(self, root: dict, path: List[str]) -> dict:
        """Navega/crea diccionarios anidados y retorna el dict final del path."""
        node = root
        for key in path:
            if key not in node or not isinstance(node[key], dict):
                node[key] = {}
            node = node[key]
        return node

    def _ensure_items_bucket(self, bucket: dict) -> dict:
        """Asegura estructura {'items': [], 'total': 0} en un bucket de elemento."""
        if "items" not in bucket or not isinstance(bucket.get("items"), list):
            bucket["items"] = []
        if "total" not in bucket or not isinstance(bucket.get("total"), (int, float)):
            bucket["total"] = 0
        return bucket

    def _extract_data_from_file(
        self,
        wb: Workbook,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        items: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []

        worksheet = wb.active
        rows = worksheet.iter_rows(
            min_row=3,
            min_col=1,
            max_col=4,
            values_only=True,
        )

        for row_number, row in enumerate(rows, start=3):
            empty_cells = [
                value is None or (isinstance(value, str) and not value.strip())
                for value in row
            ]

            if all(empty_cells):
                continue

            concept, _, sku, amount = row
            material_filter = {"sku": sku}

            missing_columns = [
                name
                for name, is_empty in zip(
                    ("SKU (C)", "Cantidad (D)"),
                    empty_cells[2:4],
                )
                if is_empty
            ]

            if missing_columns:
                errors.append({
                    "row": row_number,
                    "material": concept,
                    "message": f"Faltan valores en {', '.join(missing_columns)}.",
                })
                continue

            material = self.material_repo.find_one(
                material_filter,
                {
                    "_id": 1,
                    "supplier_id": 1,
                    "concept": 1,
                    "sku": 1,
                    "measurement": 1,
                    "presentation": 1,
                    "inventory_price": 1,
                },
            )

            if material is None:
                errors.append({
                    "row": row_number,
                    "material": concept,
                    "message": "Material no encontrado.",
                })
                continue

            inventory_price = material.get("inventory_price")

            try:
                quantity = Decimal(str(amount))
                price = Decimal(str(inventory_price))

                if not quantity.is_finite() or not price.is_finite():
                    raise InvalidOperation

                total = (quantity * price).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
            except InvalidOperation:
                errors.append({
                    "row": row_number,
                    "material": concept,
                    "message": (
                        f"Cantidad o precio inválido. "
                        f"Cantidad: {amount!r}. Precio: {inventory_price!r}."
                    ),
                })
                continue

            material_data = {
                key: value
                for key, value in material.items()
                if key not in {"_id", "inventory_price"}
            }

            items.append({
                **material_data,
                "id": str(material["_id"]),
                "color": None,
                "inventory_price": float(price),
                "amount": float(quantity),
                "total": float(total),
            })

        return items, errors

    # ────────────────────────────────────────────────────────────────────────────────
    # CÁLCULOS CENTRALES (USADO EN TODOS LOS MÉTODOS)
    # ────────────────────────────────────────────────────────────────────────────────
    def _recalculate_concept_totals(self, concept: dict) -> dict:
        """
        Recalcula subtotal, IVA y total del concepto considerando:
          - materials, production, equipment, installation
          - prov.materials, prov.equipment, prov.mo
          - templates[].total
          - indirect (porcentaje)
        """
        subtotal = Decimal("0.00")

        # 1️⃣ Totales de primer nivel
        for _, value in concept.items():
            if isinstance(value, dict) and "total" in value:
                subtotal += Decimal(str(value["total"]))

        # 2️⃣ Totales de 'prov'
        prov = concept.get("prov", {})
        if isinstance(prov, dict):
            for _, prov_value in prov.items():
                if isinstance(prov_value, dict) and "total" in prov_value:
                    subtotal += Decimal(str(prov_value["total"]))

        # 3️⃣ Totales de templates
        templates = concept.get("templates", [])
        if isinstance(templates, list):
            subtotal += sum(Decimal(str(t.get("total", 0))) for t in templates)

        # 4️⃣ Aplicar costo indirecto (%)
        indirect = Decimal(str(concept.get("indirect", 0) or 0))
        if indirect > 0:
            subtotal += (subtotal * indirect / Decimal("100"))

        # 5️⃣ IVA y total
        subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva = (subtotal * Decimal("0.16")
               ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (subtotal + iva).quantize(Decimal("0.01"),
                                          rounding=ROUND_HALF_UP)

        concept["subtotal"] = float(subtotal)
        concept["iva"] = float(iva)
        concept["total"] = float(total)
        return concept

    # ────────────────────────────────────────────────────────────────────────────────
    # CRUD BÁSICO
    # ────────────────────────────────────────────────────────────────────────────────
    def create(self, data: dict) -> str:
        self._validate_fields(data, ['project_id', 'name'])
        project = self.project_repo.find_by_id(data['project_id'])
        if not project:
            raise LookupError('El proyecto no existe o no es válido.')
        _ = self.concept_repo.insert(data)
        recalculate_project_totals.delay(data['project_id'])
        return data['name']

    def get_all(self, project_id: str):
        return self.concept_repo.find_all(
            query={'project_id': project_id}, order_field='created_at', order=-1
        )

    def get_by_id(self, concept_id: str):
        concept = self.concept_repo.find_by_id(concept_id)
        if not concept:
            raise LookupError('El concepto no existe.')

        templates = concept.get("templates", [])

        # Si no hay templates, retornar el concepto normal
        if not templates:
            return concept

        # 🔹 Extraer IDs de templates
        template_ids = [t.get("id") for t in templates if "id" in t]

        # 🔹 Buscar los templates completos
        full_templates = []
        for tid in template_ids:
            tpl = self.template_repo.find_by_id(tid)
            if tpl:
                tpl_clean = {k: v for k, v in tpl.items() if k not in [
                    "_id", "created_at", "updated_at"]}
                full_templates.append(tpl_clean)

        # 🔹 Reemplazar la lista original por los objetos completos
        concept["added_templates"] = full_templates

        return concept

    def update(self, concept_id: str, data: dict):
        concept = self.concept_repo.find_by_id(concept_id)
        if not concept:
            raise LookupError('El concepto no existe.')
        self.concept_repo.update(concept_id, data)
        recalculate_project_totals.delay(concept['project_id'])

    def delete(self, concept_id: str):
        concept = self.concept_repo.find_by_id(concept_id)
        if not concept:
            raise LookupError('El concepto no existe.')
        self.concept_repo.delete(concept_id)
        recalculate_project_totals.delay(concept['project_id'])

    # ────────────────────────────────────────────────────────────────────────────────
    # PROCESAR / ELIMINAR ITEMS
    # ────────────────────────────────────────────────────────────────────────────────
    def process_items(self, concept_id: str, element: str, item: Mapping[str, Any]) -> None:
        """Agrega o actualiza un item en cualquier ruta (incluye prov.*)."""
        if not item or "total" not in item or "id" not in item:
            raise ValueError("`item` debe incluir las claves 'id' y 'total'.")

        concept = self.concept_repo.find_by_id(concept_id)
        if not concept:
            raise ConceptNotFoundError(f"No existe el concepto: {concept_id}")

        path = [p.strip() for p in element.split(".") if p.strip()]
        if not path:
            raise ValueError("`element` no puede estar vacío.")

        bucket = self._get_path_dict(concept, path)
        bucket = self._ensure_items_bucket(bucket)

        items = bucket["items"]
        existing = next((i for i in items if i.get("id") == item["id"]), None)
        if existing:
            existing.update(dict(item))
        else:
            items.append(dict(item))

        total_bucket = sum(Decimal(str(i.get("total", 0))) for i in items)
        bucket["total"] = float(total_bucket.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP))

        top_key = path[0]
        concept[top_key] = concept.get(
            top_key, bucket if len(path) == 1 else concept[top_key])

        concept = self._recalculate_concept_totals(concept)
        self.concept_repo.update(concept_id, concept)
        recalculate_project_totals.delay(concept['project_id'])

    def delete_item(self, concept_id: str, element: str, item_id: str) -> None:
        """Elimina un item en cualquier ruta (incluye prov.*)."""
        if not element or not isinstance(element, str):
            raise ValueError("`element` debe ser una cadena válida.")

        concept = self.concept_repo.find_by_id(concept_id)
        if not concept:
            raise ConceptNotFoundError(f"No existe el concepto {concept_id}")

        path = [p.strip() for p in element.split(".") if p.strip()]
        node = concept
        for key in path[:-1]:
            node = node.get(key, {})
            if not isinstance(node, dict):
                raise ValueError(f"Estructura inválida en '{key}'.")

        target_key = path[-1]
        element_value = node.get(target_key, {"items": [], "total": 0})
        if not isinstance(element_value, dict) or "items" not in element_value:
            raise ValueError(
                f"El elemento '{element}' no tiene estructura válida.")

        items = element_value.get("items", [])
        new_items = [i for i in items if str(i.get("id")) != str(item_id)]

        if new_items:
            total = sum(Decimal(str(i.get("total", 0))) for i in new_items)
            element_value["items"] = new_items
            element_value["total"] = float(total.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP))
        else:
            element_value = {"items": [], "total": 0.0}

        node[target_key] = element_value
        concept = self._recalculate_concept_totals(concept)
        self.concept_repo.update(concept_id, concept)
        recalculate_project_totals.delay(concept['project_id'])

    # ────────────────────────────────────────────────────────────────────────────────
    # PLANTILLAS (TEMPLATES)
    # ────────────────────────────────────────────────────────────────────────────────
    def process_templates(self, concept_id: str, templates: list[dict]) -> None:
        """Reemplaza templates y recalcula totales globales."""
        concept = self.concept_repo.find_by_id(concept_id)
        if not concept:
            raise LookupError(f"El concepto con id={concept_id} no existe")

        if not isinstance(templates, list):
            raise ValueError(
                "`templates` debe ser una lista con 'id' y 'total'.")

        cleaned = []
        for t in templates:
            if not isinstance(t, dict) or "id" not in t or "total" not in t:
                raise ValueError(f"Formato inválido en template: {t}")
            cleaned.append({"id": t["id"], "total": float(t["total"])})

        concept["templates"] = cleaned
        concept = self._recalculate_concept_totals(concept)
        self.concept_repo.update(concept_id, concept)
        recalculate_project_totals.delay(concept['project_id'])

    # ────────────────────────────────────────────────────────────────────────────────
    # COSTOS INDIRECTOS
    # ────────────────────────────────────────────────────────────────────────────────
    def process_indirect_costs(self, concept_id: str, indirect: float) -> None:
        """Aplica un porcentaje de costos indirectos y recalcula totales."""
        concept = self.concept_repo.find_by_id(concept_id)
        if not concept:
            raise ConceptNotFoundError(f"No existe el concepto {concept_id}")

        try:
            indirect_value = Decimal(str(indirect or 0))
        except Exception:
            raise ValueError(f"Valor inválido de indirecto: {indirect}")

        concept["indirect"] = float(indirect_value)
        concept = self._recalculate_concept_totals(concept)
        self.concept_repo.update(concept_id, concept)
        recalculate_project_totals.delay(concept['project_id'])

    def clear_indirect_costs(self, concept_id: str) -> None:
        """Limpia los costos indirectos y recalcula totales."""
        concept = self.concept_repo.find_by_id(concept_id)
        if not concept:
            raise ConceptNotFoundError(f"No existe el concepto {concept_id}")

        concept["indirect"] = None
        concept = self._recalculate_concept_totals(concept)
        self.concept_repo.update(concept_id, concept)
        recalculate_project_totals.delay(concept['project_id'])

    # ────────────────────────────────────────────────────────────────────────────────
    # UPLOAD MATERIALS BY FILE
    # ────────────────────────────────────────────────────────────────────────────────
    def upload(self, concept_id: str, path: str, request_file):
        if not concept_id:
            raise ValidationError("El ID del concepto es obligatorio.")

        if not ObjectId.is_valid(concept_id):
            raise ValidationError("El ID del concepto es inválido.")

        if not path:
            raise ValidationError(
                "La sección donde se cargarán los materiales es obligatoria."
            )

        if path not in {"materials", "equipment"}:
            raise ValidationError("La sección indicada es inválida.")

        if not request_file:
            raise ValidationError("El archivo es requerido.")

        concept = self.concept_repo.find_one(
            {"_id": ObjectId(concept_id)},
            {"_id": 0, "project_id": 1, "materials": 1, "equipment": 1},
        )
        if concept is None:
            raise ValidationError("El concepto no existe.")

        try:
            workbook = load_workbook(request_file, data_only=True)
        except (InvalidFileException, BadZipFile, OSError, ValueError) as exc:
            raise ValidationError(f"Archivo Excel inválido: {exc}") from exc

        try:
            new_items, errors = self._extract_data_from_file(workbook)
        finally:
            workbook.close()

        section = concept.setdefault(path, {})
        items = section.get("items", [])

        items_by_id = {item["id"]: item for item in items}
        new_items_by_id = {item["id"]: item for item in new_items}

        num_inserted = 0
        num_updated = 0

        for item_id, new_item in new_items_by_id.items():
            if item_id not in items_by_id:
                num_inserted += 1
            elif items_by_id[item_id] != new_item:
                num_updated += 1

            items_by_id[item_id] = new_item

        updated_items = list(items_by_id.values())

        total_items = sum(
            (Decimal(str(item.get("total", 0))) for item in updated_items),
            Decimal("0.00"),
        )

        section["items"] = updated_items
        section["total"] = float(
            total_items.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

        concept = self._recalculate_concept_totals(concept)
        self.concept_repo.update(concept_id, concept)
        recalculate_project_totals.delay(concept["project_id"])

        return {
            "num_inserted": num_inserted,
            "num_updated": num_updated,
            "errors": errors,
        }
