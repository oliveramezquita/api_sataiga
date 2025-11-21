from urllib.parse import parse_qs
from api.constants import DEFAULT_PAGE_SIZE


def get_query_params(request):
    """
    Extrae TODOS los parámetros de query de un request de forma robusta.
    - Devuelve dict plano con valores ya convertidos (int, bool, str)
    - Incluye page, page_size, q, sort_by y order_by (asc=>1, desc=>-1)
    """
    if not request:
        return {"page": 1, "page_size": DEFAULT_PAGE_SIZE, "q": None, "sort_by": None, "order_by": 1}

    try:
        # Soporte DRF o WSGI nativo
        query_params = getattr(request, "query_params", None) or parse_qs(
            request.META.get("QUERY_STRING", ""))

        params = {}

        def convert_value(value):
            """Convierte strings a bool/int/float/str automáticamente."""
            if value is None:
                return None
            if isinstance(value, list):
                value = value[0]

            # Booleanos
            if isinstance(value, str) and value.lower() in {"true", "false"}:
                return value.lower() == "true"

            # Números
            try:
                if isinstance(value, str) and "." in value:
                    return float(value)
                return int(value)
            except (ValueError, TypeError):
                return value.strip() if isinstance(value, str) else value

        # Extrae todos los parámetros
        for key, value in query_params.items():
            params[key] = convert_value(value)

        # Valores por defecto
        params.setdefault("page", 1)
        params.setdefault("page_size", params.pop(
            "itemsPerPage", DEFAULT_PAGE_SIZE))
        params.setdefault("q", None)
        params.setdefault("sort_by", params.pop("sortBy", None))

        # --- Normaliza order_by ---
        raw_order = params.pop("orderBy", None)

        if raw_order is None:
            order_value = 1  # default ascendente
        elif str(raw_order).lower() == "desc":
            order_value = -1
        else:  # incluye 'asc' o cualquier otro valor inválido
            order_value = 1

        params["order_by"] = order_value

        return params

    except Exception:
        return {"page": 1, "page_size": DEFAULT_PAGE_SIZE, "q": None, "sort_by": None, "order_by": 1}
