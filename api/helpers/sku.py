import re
from pymongo.errors import DuplicateKeyError

SKU_SUFFIX_RE = re.compile(r"^(.*?)(?:-(\d+))?$")


def normalize_sku(sku: str) -> str:
    return (sku or "").strip().upper()


def split_base_and_n(sku: str) -> tuple[str, int | None]:
    sku = normalize_sku(sku)
    m = SKU_SUFFIX_RE.match(sku)
    base = (m.group(1) or "").strip() if m else sku
    n = int(m.group(2)) if m and m.group(2) else None
    return base, n


def with_unique_sku(desired_sku: str, op_fn, max_attempts: int = 50):
    """
    op_fn(candidate_sku) hace insert/update y debe lanzar DuplicateKeyError si sku ya existe.
    Retorna lo que op_fn retorne.
    """
    base, n = split_base_and_n(desired_sku)
    if not base:
        raise ValueError("SKU inválido.")

    # sin sufijo: base, base-1, base-2...
    if n is None:
        candidate = base
        next_n = 1
    else:
        candidate = f"{base}-{n}"
        next_n = n + 1

    for _ in range(max_attempts):
        try:
            return op_fn(candidate)
        except DuplicateKeyError:
            candidate = f"{base}-{next_n}"
            next_n += 1

    raise ValueError(
        "No se pudo generar un SKU único (demasiados duplicados).")
