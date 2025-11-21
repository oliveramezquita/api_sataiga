import hashlib
import json
from functools import wraps
from django.core.cache import cache
from bson import ObjectId
from datetime import datetime, date
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# Función auxiliar para serializar datos no JSON-compatibles
# -------------------------------------------------------------


def _safe_json(obj):
    """
    Serializador seguro para tipos usados comúnmente en MongoDB.
    Convierte ObjectId, datetime, Decimal, etc. en tipos válidos para JSON.
    """
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (set, tuple)):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="ignore")
    if isinstance(obj, dict):
        return {k: _safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_json(v) for v in obj]
    return obj


# -------------------------------------------------------------
# Decorador de cache con hash dinámico + serialización segura
# -------------------------------------------------------------
def cache_result(prefix: str, ttl: int = 300):
    """
    Crea una clave de cache única basada en los args/kwargs y serializa
    los resultados de forma segura (para evitar errores con ObjectId, etc.).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 🔹 Generar clave hash única basada en args/kwargs
            try:
                key_data = json.dumps(
                    {"args": args[1:], "kwargs": kwargs},
                    sort_keys=True,
                    default=_safe_json,  # ✅ usa _safe_json
                )
            except Exception as e:
                logger.warning(
                    f"[cache_result] No se pudo serializar args: {e}")
                key_data = str(args[1:]) + str(kwargs)

            hash_key = hashlib.md5(key_data.encode()).hexdigest()
            cache_key = f"{prefix}:{hash_key}"

            # 🔹 Intentar leer del cache
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data

            # 🔹 Ejecutar función y serializar el resultado
            result = func(*args, **kwargs)
            try:
                json_safe_result = _safe_json(result)
                cache.set(cache_key, json_safe_result, ttl)
            except Exception as e:
                logger.warning(
                    f"[cache_result] No se pudo cachear resultado: {e}")

            return result

        return wrapper
    return decorator


# -------------------------------------------------------------
# Invalida cache (por prefijo)
# -------------------------------------------------------------
def invalidate_cache(prefix: str):
    """
    Elimina todas las claves de cache que comiencen con el prefijo.
    Ejemplo:
        invalidate_cache('catalog')
    """
    try:
        deleted = cache.delete_pattern(f"{prefix}:*")
        logger.info(
            f"[invalidate_cache] Cleared cache for prefix '{prefix}' ({deleted} keys)")
    except Exception as e:
        logger.warning(
            f"[invalidate_cache] Error clearing prefix '{prefix}': {e}")
