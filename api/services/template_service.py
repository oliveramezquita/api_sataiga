from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Any, Optional, Dict
from api.repositories.template_repository import TemplateRepository
from api.repositories.client_repository import ClientRepository
from api.services.base_service import BaseService


class TemplateNotFoundError(Exception):
    pass


class TemplateService(BaseService):
    """Lógica de negocio pura para Templates."""

    CACHE_PREFIX = "templates"

    def __init__(self):
        self.template_repo = TemplateRepository()
        self.client_repo = ClientRepository()

    # ----------------------------------------------------------
    # CREAR PLANTILLA
    # ----------------------------------------------------------
    def create(self, data: Dict[str, Any]) -> str:
        """
        Crea una plantilla validando cliente y campos requeridos.
        """
        self._validate_fields(data, ["name"])

        # Validar cliente si viene definido
        if "client_id" in data:
            client = self.client_repo.find_by_id(
                data["client_id"], {"type": "PE"})
            if not client:
                raise LookupError(
                    "El cliente seleccionado no existe o no es válido.")

        template_id = self._create(
            repo=self.template_repo,
            data=data,
            required_fields=["name"],
            cache_prefix=self.CACHE_PREFIX,
        )

        return str(template_id)

    # ----------------------------------------------------------
    # LECTURAS
    # ----------------------------------------------------------
    def get_all(self, client_id: Optional[str] = None):
        """
        Devuelve todas las plantillas, opcionalmente filtradas por client_id.
        """
        filters = {}
        if client_id:
            filters["$or"] = [{"client_id": client_id}, {"client_id": None}]
        return self._get_all_cached(self.template_repo, filters, prefix=self.CACHE_PREFIX)

    def get_by_id(self, template_id: str):
        """Obtiene una plantilla por ID (usa método genérico del BaseService)."""
        return self._get_by_id(self.template_repo, template_id)

    # ----------------------------------------------------------
    # ACTUALIZAR Y ELIMINAR
    # ----------------------------------------------------------
    def update(self, template_id: str, data: Dict[str, Any]) -> str:
        """Actualiza una plantilla existente."""
        self._update(self.template_repo, template_id,
                     data, cache_prefix=self.CACHE_PREFIX)
        return "Plantilla actualizada correctamente."

    def delete(self, template_id: str) -> str:
        """Elimina una plantilla existente."""
        self._delete(self.template_repo, template_id,
                     cache_prefix=self.CACHE_PREFIX)
        return "Plantilla eliminada correctamente."

    # ----------------------------------------------------------
    # VALIDACIONES Y UTILIDADES
    # ----------------------------------------------------------
    def _validate_element_name(self, element: str):
        """
        Valida nombres de campo seguros para MongoDB.
        """
        if not element or not isinstance(element, str):
            raise ValueError(
                "El nombre del 'element' es obligatorio y debe ser str.")
        if "." in element or "$" in element:
            raise ValueError(
                "El nombre del 'element' no puede contener '.' ni '$'.")

    # ----------------------------------------------------------
    # PROCESAMIENTO DE ITEMS
    # ----------------------------------------------------------
    def process_items(self, template_id: str, element: str, item: Mapping[str, Any]) -> None:
        """
        Agrega o actualiza un item dentro de template[element].items.
        Recalcula totales locales y globales.
        """
        self._validate_element_name(element)
        template = self._get_by_id(self.template_repo, template_id)

        if not item or "total" not in item or "id" not in item:
            raise ValueError("`item` debe incluir las claves 'id' y 'total'.")

        element_value: Optional[Dict[str, Any]] = template.get(element) or {
            "items": [], "total": 0}
        items = element_value.get("items", [])

        # Actualizar o agregar
        existing_item = next((i for i in items if i["id"] == item["id"]), None)
        if existing_item:
            existing_item.update(item)
        else:
            items.append(dict(item))

        # Recalcular totales del elemento y globales
        element_value["items"] = items
        element_value["total"] = self._sum_totals(items)

        # Recalcular totales globales
        subtotal, iva, total = self._recalculate_global_totals(template)

        # Persistir cambios
        update = {
            element: element_value,
            "subtotal": float(subtotal),
            "iva": float(iva),
            "total": float(total),
        }
        self.template_repo.update(template_id, update)

    def delete_item(self, template_id: str, element: str, item_id: str) -> None:
        """
        Elimina un item dentro de template[element].items según su ID.
        Luego recalcula los totales locales y globales.
        """
        self._validate_element_name(element)
        template = self._get_by_id(self.template_repo, template_id)

        element_value: Optional[Dict[str, Any]] = template.get(element)
        if not isinstance(element_value, dict) or "items" not in element_value:
            raise ValueError(
                f"El elemento '{element}' no tiene estructura válida.")

        items = [i for i in element_value.get(
            "items", []) if str(i.get("id")) != str(item_id)]
        element_value["items"] = items
        element_value["total"] = self._sum_totals(items)

        subtotal, iva, total = self._recalculate_global_totals(template)

        update = {
            element: element_value,
            "subtotal": float(subtotal),
            "iva": float(iva),
            "total": float(total),
        }
        self.template_repo.update(template_id, update)

    # ----------------------------------------------------------
    # PROCESAMIENTO DE COSTOS INDIRECTOS
    # ----------------------------------------------------------
    def process_indirect_costs(self, template_id: str, indirect_costs: Any) -> None:
        """
        Agrega o actualiza los costos indirectos de una plantilla y recalcula los totales.
        """
        template = self._get_by_id(self.template_repo, template_id)
        try:
            indirect = Decimal(str(indirect_costs or 0))
        except Exception:
            raise ValueError(f"Valor de indirectos inválido: {indirect_costs}")

        # Totales base
        base_total = sum(
            Decimal(str(template.get(section, {}).get("total", 0)))
            for section in ["production", "equipment", "materials"]
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        indirect_value = (base_total * indirect / Decimal("100")
                          ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        new_subtotal = base_total + indirect_value
        iva = (new_subtotal * Decimal("0.16")
               ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = new_subtotal + iva

        update_data = {
            "indirect": float(indirect),
            "subtotal": float(new_subtotal),
            "iva": float(iva),
            "total": float(total),
        }
        self.template_repo.update(template_id, update_data)

    def clear_indirect_costs(self, template_id: str) -> None:
        """
        Limpia los costos indirectos y recalcula los totales base.
        """
        template = self._get_by_id(self.template_repo, template_id)

        base_total = sum(
            Decimal(str(template.get(section, {}).get("total", 0) or 0))
            for section in ["production", "equipment", "materials"]
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        iva = (base_total * Decimal("0.16")
               ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = base_total + iva

        update_data = {
            "indirect": None,
            "subtotal": float(base_total),
            "iva": float(iva),
            "total": float(total),
        }
        self.template_repo.update(template_id, update_data)

    # ----------------------------------------------------------
    # HELPERS INTERNOS
    # ----------------------------------------------------------
    def _sum_totals(self, items: list[Dict[str, Any]]) -> float:
        """Suma totales de una lista de items y devuelve el resultado redondeado."""
        total = sum(Decimal(str(i["total"])) for i in items)
        return float(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    def _recalculate_global_totals(self, template: Dict[str, Any]):
        """Recalcula subtotal, IVA y total global en base a todos los elementos."""
        subtotal = Decimal("0.00")
        for _, value in template.items():
            if isinstance(value, dict) and "total" in value:
                subtotal += Decimal(str(value["total"]))
        subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva = (subtotal * Decimal("0.16")
               ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (subtotal + iva).quantize(Decimal("0.01"),
                                          rounding=ROUND_HALF_UP)
        return subtotal, iva, total
