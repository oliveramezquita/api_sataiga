import re
import uuid
from api.repositories.project_repository import ProjectRepository
from api.repositories.client_repository import ClientRepository
from api.repositories.concept_repository import ConceptRepository
from decimal import Decimal, ROUND_HALF_UP


class ProjectService:
    """Lógica de negocio pura para Proyectos."""

    def __init__(self):
        self.project_repo = ProjectRepository()
        self.client_repo = ClientRepository()
        self.concept_repo = ConceptRepository()

    def _validate_fields(self, data: dict, required_fields: list[str]):
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise ValueError(
                f'Campos requeridos faltantes: {", ".join(missing)}')

    def create(self, data: dict) -> str:
        self._validate_fields(data, ['client_id', 'name', 'front'])
        client = self.client_repo.find_valid_client(data['client_id'])
        if not client:
            raise LookupError(
                'El cliente seleccionado no existe o no es válido.')

        project_data = {
            **data,
            'version': 1,
            'status': 0
        }
        project_id = self.project_repo.insert(project_data)
        return str(project_id)

    def get_all(self):
        return self.project_repo.find_all(order_field='created_at', order=-1)

    def get_by_id(self, project_id: str):
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise LookupError('El proyecto no existe.')
        return project

    def update(self, project_id: str, data: dict):
        """
        Actualiza los datos de un proyecto y, si viene el anticipo (advance),
        recalcula automáticamente la liquidación y el saldo (balance).
        """
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise LookupError("El proyecto no existe.")

        # 🔹 Si viene un anticipo nuevo, recalculamos la liquidación
        if "advance" in data and data['advance']:
            # Convertir valores actuales a Decimal con seguridad
            subtotal = Decimal(str(project.get("subtotal", 0) or 0))
            iva = Decimal(str(project.get("iva", 0) or 0))
            total = (subtotal + iva).quantize(Decimal("0.01"),
                                              rounding=ROUND_HALF_UP)

            # Obtener valores actuales o nuevos del anticipo y liquidación
            advance = Decimal(
                str(data.get("advance", project.get("advance", 0) or 0)))
            data['liquidation'] = float(total)

            # 🔹 Calcular balance siempre (saldo pendiente)
            balance = (total - advance).quantize(Decimal("0.01"),
                                                 rounding=ROUND_HALF_UP)
            data["balance"] = float(balance)

        # 🔹 Ejecutar la actualización
        self.project_repo.update(project_id, data)

    def delete(self, project_id: str):
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise LookupError('El proyecto no existe.')
        self.project_repo.delete(project_id)

    def get_clients(self, query: str = None):
        """Devuelve lista de clientes tipo PE filtrados por nombre, dirección o email."""
        clients = self.client_repo.find_pe_clients(query)
        results = []

        for client in clients:
            client_id = str(client["_id"])
            projects = self.project_repo.find_all({"client_id": client_id})

            total_projects = len(projects)

            # Contadores por estatus
            status_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
            for p in projects:
                status = p.get("status")
                if status in status_counts:
                    status_counts[status] += 1

            project_data = [
                {
                    "id": uuid.uuid4().hex,
                    "color": "secondary",
                    "icon": "tabler-color-picker",
                    "title": "Diseño",
                    "count": status_counts[0],
                },
                {
                    "id": uuid.uuid4().hex,
                    "color": "warning",
                    "icon": "tabler-cash-register",
                    "title": "Cotización",
                    "count": status_counts[1],
                },
                {
                    "id": uuid.uuid4().hex,
                    "color": "info",
                    "icon": "tabler-building-factory-2",
                    "title": "Producción",
                    "count": status_counts[2],
                },
                {
                    "id": uuid.uuid4().hex,
                    "color": "primary",
                    "icon": "tabler-package-export",
                    "title": "Instalación",
                    "count": status_counts[3],
                },
                {
                    "id": uuid.uuid4().hex,
                    "color": "success",
                    "icon": "tabler-checklist",
                    "title": "Entregado",
                    "count": status_counts[4],
                },
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

    def get_clone_name(self, client_id: str, name: str) -> str:
        # 🔹 1. Obtener todos los nombres de proyectos del cliente
        projects = self.project_repo.find_all({"client_id": client_id})
        project_names = [p.get("name", "") for p in projects]

        # 🔹 2. Normalizar y buscar coincidencias del nombre base
        pattern = re.compile(
            rf"^{re.escape(name)}(?: clon (\d+))?$", re.IGNORECASE)

        # Encontrar todos los nombres que coincidan con el patrón
        clone_numbers = []
        for existing_name in project_names:
            match = pattern.match(existing_name)
            if match:
                # Si es "Vivienda completa" sin clon → 0
                if not match.group(1):
                    clone_numbers.append(0)
                else:
                    clone_numbers.append(int(match.group(1)))

        # 🔹 3. Calcular el siguiente consecutivo
        next_clone_number = max(clone_numbers) + 1 if clone_numbers else 1

        # 🔹 4. Retornar el nuevo nombre
        new_name = f"{name} clon {next_clone_number}"
        return new_name

    def clone_project(self, project_id: str, new_name: str = None):
        """
        Crea un clon de un proyecto existente, con un nombre nuevo.
        Si no se proporciona un nombre, se genera automáticamente usando get_clone_name().
        """
        # 🔹 1. Obtener proyecto original
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise LookupError(f"El proyecto {project_id} no existe.")

        client_id = project["client_id"]

        # 🔹 2. Determinar el nuevo nombre
        if not new_name:
            base_name = project["name"]
            new_name = self.get_clone_name(client_id, base_name)

        # 🔹 3. Clonar los datos del proyecto (excluyendo _id, created_at, updated_at)
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

        # 🔹 4. Insertar el nuevo proyecto
        new_project_id = self.project_repo.insert(project_clone)

        # 🔹 5. Clonar conceptos asociados (si existen)
        concepts = self.concept_repo.find_all({"project_id": project_id})
        for concept in concepts:
            concept_copy = concept.copy()
            concept_copy["project_id"] = str(new_project_id)
            self.concept_repo.insert({k: v for k, v in concept_copy.items() if k not in [
                                     "_id", "created_at", "updated_at"]})
