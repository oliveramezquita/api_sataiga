from typing import Any, Dict, List, Optional, Callable
from django.core.paginator import Paginator
from api.utils.cache_utils import invalidate_cache, cache_result


class BaseService:
    """Métodos utilitarios comunes y reutilizables para todos los servicios."""

    # ----------------------------------------------------------
    # VALIDACIONES
    # ----------------------------------------------------------
    def _validate_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Verifica que los campos requeridos estén presentes y no sean vacíos.
        Lanza ValueError si faltan.
        """
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            raise ValueError(
                f"Campos requeridos faltantes: {', '.join(missing)}")

    # ----------------------------------------------------------
    # OPERACIONES CRUD GENÉRICAS
    # ----------------------------------------------------------
    def _create(
        self,
        repo: Any,
        data: Dict[str, Any],
        required_fields: Optional[List[str]] = None,
        cache_prefix: Optional[str] = None,
        preprocess: Optional[Callable[[
            Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> Any:
        """
        Crea un documento genéricamente:
        - Valida campos requeridos.
        - Aplica preprocesamiento opcional.
        - Inserta en el repositorio.
        - Invalida cache si se especifica.
        """
        if required_fields:
            self._validate_fields(data, required_fields)

        if preprocess:
            data = preprocess(data)

        result = repo.insert(data)

        if cache_prefix:
            invalidate_cache(cache_prefix)

        return result

    def _update(
        self,
        repo: Any,
        _id: str,
        data: Dict[str, Any],
        cache_prefix: Optional[str] = None,
    ) -> None:
        """
        Actualiza un documento genéricamente.
        Lanza LookupError si el documento no existe.
        """
        existing = repo.find_by_id(_id)
        if not existing:
            raise LookupError("El registro no existe.")

        repo.update(_id, data)

        if cache_prefix:
            invalidate_cache(cache_prefix)

    def _delete(
        self,
        repo: Any,
        _id: str,
        cache_prefix: Optional[str] = None,
    ) -> None:
        """
        Elimina un documento genéricamente.
        Lanza LookupError si el documento no existe.
        """
        existing = repo.find_by_id(_id)
        if not existing:
            raise LookupError("El registro no existe.")

        repo.delete(_id)

        if cache_prefix:
            invalidate_cache(cache_prefix)

    # ----------------------------------------------------------
    # LECTURAS Y CACHE
    # ----------------------------------------------------------
    def _get_all_cached(
        self,
        repo,
        filters=None,
        prefix="",
        ttl=300,
        order_field=None,
        order=1
    ):
        """
        Obtiene una lista cacheada de documentos según filtros y orden.
        ✅ Cada combinación única de filtros/orden genera una clave distinta.
        ✅ Compatible con el decorador cache_result(prefix, ttl).
        """

        @cache_result(prefix=prefix, ttl=ttl)
        def _cached(repo_ref, filters_ref, order_field_ref, order_ref):
            data = repo_ref.find_all(
                filters_ref or {}, order_field_ref, order_ref)
            return data

        # 🔹 Ahora todos los parámetros relevantes afectan la clave de cache
        result = _cached(repo, filters, order_field, order)

        return result

    def _get_by_id(self, repo: Any, _id: str, serializer: Optional[Callable] = None):
        """Obtiene un documento por ID, opcionalmente serializándolo."""
        doc = repo.find_by_id(_id)
        if not doc:
            raise LookupError("El registro no existe.")
        return serializer(doc).data if serializer else doc

    # ----------------------------------------------------------
    # PAGINACIÓN GENÉRICA
    # ----------------------------------------------------------
    def _paginate(self, items: List[Dict[str, Any]], page: int, page_size: int, serializer: Optional[Callable] = None):
        """Aplica paginación con Django Paginator y opcionalmente serializa."""
        paginator = Paginator(items, per_page=page_size)
        page_obj = paginator.get_page(page)
        data = serializer(page_obj.object_list,
                          many=True).data if serializer else page_obj.object_list

        return {
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page_obj.number,
            "results": data,
        }
