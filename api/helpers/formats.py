import re
import math
import unicodedata
from bson import ObjectId
from datetime import datetime
from typing import Any


def clean_text(text):
    clean = re.sub(r'[^a-zA-Z]', '', text)
    return clean


def to_float(value: Any, default: float = 0.0, *, min_value: float = None) -> float:
    try:
        n = round(float(value), 2)
        if not math.isfinite(n):
            return default
        if min_value is not None and n < min_value:
            return default
        return n
    except (TypeError, ValueError):
        return default


def mongo_to_json(value):
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, list):
        return [mongo_to_json(v) for v in value]

    if isinstance(value, dict):
        return {k: mongo_to_json(v) for k, v in value.items()}

    return value


def to_number(val) -> float:
    """
    Reglas:
    - vacío / None / espacios => 0
    - string / NaN / Null => 0
    - '.5' => 0.5
    - no aceptar negativos => 0
    - cualquier cosa inválida => 0
    """
    if val is None:
        return 0.0

    if isinstance(val, (int, float)):
        v = float(val)
        if math.isnan(v) or math.isinf(v) or v < 0:
            return 0.0
        return v

    if isinstance(val, str):
        s = val.strip()
        if not s:
            return 0.0

        s = s.replace(" ", "")
        if s.lower() in {"nan", "null", "none"}:
            return 0.0

        # ".5" => "0.5"
        if s.startswith("."):
            s = "0" + s

        # opcional: "1,25" => "1.25"
        if re.fullmatch(r"-?\d+,\d+", s):
            s = s.replace(",", ".")

        try:
            v = float(s)
        except ValueError:
            return 0.0

        if math.isnan(v) or math.isinf(v) or v < 0:
            return 0.0
        return v

    return 0.0


def normalize_num(v: float):
    v = round(float(v), 2)
    # si es entero, regresarlo como int para que se vea como tus ejemplos
    return int(v) if abs(v - round(v)) < 1e-9 else v


def normalize_strict(s: str) -> str:
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = s.casefold()
    s = re.sub(r'\s+', ' ', s).strip()
    s = re.sub(r'\s*\+\s*', ' + ', s)  # normaliza espacios alrededor de +
    return s
