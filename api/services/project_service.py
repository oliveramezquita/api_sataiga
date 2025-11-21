import re
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from api.services.base_service import BaseService
from api.repositories.project_repository import ProjectRepository
from api.repositories.client_repository import ClientRepository
from api.repositories.concept_repository import ConceptRepository


class ProjectService(BaseService):
    """Lógica de negocio pura para Proyectos."""

    CACHE_PREFIX = "projects"

    def __init__(self):
        self.project_repo = ProjectRepository()
        self.client_repo = ClientRepository()
        self.concept_repo = ConceptRepository()

    # ----------------------------------------------------------
    # CREAR PROYECTO
    # ----------------------------------------------------------
    def create(self, data: Dict[str, Any]) -> str:
        """
        Crea un nuevo proyecto, validando cliente y campos requeridos.
        """
        self._validate_fields(data, ["client_id", "name", "front"])

        client = self.client_repo.find_by_id(data["client_id"], {"type": "PE"})
        if not client:
            raise LookupError(
                "El cliente seleccionado no existe o no es válido.")

        project_data = {**data, "version": 1, "status": 0}
        project_id = self._create(
            repo=self.project_repo,
            data=project_data,
            required_fields=["client_id", "name", "front"],
            cache_prefix=self.CACHE_PREFIX,
        )
        return str(project_id)

    # ----------------------------------------------------------
    # LECTURAS
    # ----------------------------------------------------------
    def get_all(self):
        """Obtiene todos los proyectos ordenados por fecha de creación."""
        return self.project_repo.find_all(order_field="created_at", order=-1)

    def get_by_id(self, project_id: str):
        """Obtiene un proyecto por ID (usando método base)."""
        return self._get_by_id(self.project_repo, project_id)

    # ----------------------------------------------------------
    # ACTUALIZAR PROYECTO
    # ----------------------------------------------------------
    def update(self, project_id: str, data: Dict[str, Any]) -> str:
        """
        Actualiza los datos de un proyecto y recalcula balances si viene un anticipo.
        """
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise LookupError("El proyecto no existe.")

        # 🔹 Si viene un anticipo nuevo, recalculamos la liquidación
        if "advance" in data and data["advance"]:
            subtotal = Decimal(str(project.get("subtotal", 0) or 0))
            iva = Decimal(str(project.get("iva", 0) or 0))
            total = (subtotal + iva).quantize(Decimal("0.01"),
                                              rounding=ROUND_HALF_UP)

            advance = Decimal(
                str(data.get("advance", project.get("advance", 0) or 0)))
            data["liquidation"] = float(total)

            balance = (total - advance).quantize(Decimal("0.01"),
                                                 rounding=ROUND_HALF_UP)
            data["balance"] = float(balance)

        self._update(self.project_repo, project_id, data,
                     cache_prefix=self.CACHE_PREFIX)
        return "Proyecto actualizado correctamente."

    # ----------------------------------------------------------
    # ELIMINAR PROYECTO
    # ----------------------------------------------------------
    def delete(self, project_id: str) -> str:
        """Elimina un proyecto existente (usa método base)."""
        self._delete(self.project_repo, project_id,
                     cache_prefix=self.CACHE_PREFIX)
        return "Proyecto eliminado correctamente."

    # ----------------------------------------------------------
    # CLIENTES Y RESUMEN DE PROYECTOS
    # ----------------------------------------------------------
    def get_clients(self) -> List[Dict[str, Any]]:
        """Devuelve lista de clientes tipo PE con resumen de sus proyectos."""
        clients = self.client_repo.find_all({"type": "PE"}, "pe_id")
        results: List[Dict[str, Any]] = []

        for client in clients:
            client_id = str(client["_id"])
            projects = self.project_repo.find_all({"client_id": client_id})
            total_projects = len(projects)

            # Contadores por estatus
            status_counts = {i: 0 for i in range(5)}
            for p in projects:
                status = p.get("status")
                if status in status_counts:
                    status_counts[status] += 1

            project_data = [
                {"id": uuid.uuid4().hex, "color": "secondary", "icon": "tabler-color-picker",
                 "title": "Diseño", "count": status_counts[0]},
                {"id": uuid.uuid4().hex, "color": "warning", "icon": "tabler-cash-register",
                 "title": "Cotización", "count": status_counts[1]},
                {"id": uuid.uuid4().hex, "color": "info", "icon": "tabler-building-factory-2",
                 "title": "Producción", "count": status_counts[2]},
                {"id": uuid.uuid4().hex, "color": "primary", "icon": "tabler-package-export",
                 "title": "Instalación", "count": status_counts[3]},
                {"id": uuid.uuid4().hex, "color": "success", "icon": "tabler-checklist",
                 "title": "Entregado", "count": status_counts[4]},
            ]

            results.append({
                "_id": client_id,
                "name": client["name"],
                "type": client["type"],
                "pe_id": client.get("pe_id"),
                "total_projects": total_projects,
                "project_data": project_data,
            })

        return results

    # ----------------------------------------------------------
    # CLONACIÓN DE PROYECTOS
    # ----------------------------------------------------------
    def get_clone_name(self, client_id: str, name: str) -> str:
        """Genera el siguiente nombre disponible para un clon de proyecto."""
        projects = self.project_repo.find_all({"client_id": client_id})
        project_names = [p.get("name", "") for p in projects]

        pattern = re.compile(
            rf"^{re.escape(name)}(?: clon (\d+))?$", re.IGNORECASE)
        clone_numbers = [
            int(match.group(1)) if match.group(1) else 0
            for n in project_names
            if (match := pattern.match(n))
        ]
        next_clone_number = max(clone_numbers) + 1 if clone_numbers else 1
        return f"{name} clon {next_clone_number}"

    def clone_project(self, project_id: str, new_name: Optional[str] = None):
        """
        Crea un clon de un proyecto existente, junto con sus conceptos asociados.
        """
        project = self._get_by_id(self.project_repo, project_id)
        client_id = project["client_id"]

        # Determinar nuevo nombre
        base_name = project["name"]
        new_name = new_name or self.get_clone_name(client_id, base_name)

        # Crear el clon
        project_clone = {
            "client_id": client_id,
            "version": "1",
            "name": new_name,
            "front": project.get("front"),
            "location": project.get("location"),
            "status": 0,
            "subtotal": project.get("subtotal", 0),
            "iva": project.get("iva", 0),
            "total": project.get("total", 0),
        }

        new_project_id = self.project_repo.insert(project_clone)

        # Clonar conceptos
        concepts = self.concept_repo.find_all({"project_id": project_id})
        for concept in concepts:
            concept_copy = {k: v for k, v in concept.items() if k not in [
                "_id", "created_at", "updated_at"]}
            concept_copy["project_id"] = str(new_project_id)
            self.concept_repo.insert(concept_copy)

        return str(new_project_id)
