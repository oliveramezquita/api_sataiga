from celery import shared_task
from decimal import Decimal, ROUND_HALF_UP
from api.repositories.concept_repository import ConceptRepository
from api.repositories.project_repository import ProjectRepository
import logging

logger = logging.getLogger(__name__)


@shared_task
def recalculate_project_totals(project_id: str):
    """
    Recalcula subtotal, IVA y total del proyecto
    sumando los subtotales de todos sus conceptos.
    """
    try:
        concept_repo = ConceptRepository()
        project_repo = ProjectRepository()

        concepts = concept_repo.find_all({"project_id": project_id})
        subtotal = Decimal("0.00")

        for c in concepts:
            if c.get("subtotal"):
                subtotal += Decimal(str(c["subtotal"]))

        iva = (subtotal * Decimal("0.16")
               ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (subtotal + iva).quantize(Decimal("0.01"),
                                          rounding=ROUND_HALF_UP)

        project_repo.update(
            project_id,
            {
                "subtotal": float(subtotal),
                "iva": float(iva),
                "total": float(total)
            }
        )

        logger.info(
            f"✅ Proyecto {project_id} recalculado: subtotal={subtotal}, iva={iva}, total={total}")

    except Exception as e:
        logger.error(
            f"❌ Error recalculando totales de proyecto {project_id}: {e}", exc_info=True)
        raise
