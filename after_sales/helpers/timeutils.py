from datetime import datetime, timezone


def utcnow():
    """Ahora, siempre timezone-aware en UTC."""
    return datetime.now(timezone.utc)


def to_utc(value):
    """
    Normaliza a UTC aware. pymongo devuelve datetimes naive (asumidos UTC);
    también toleramos valores ya aware.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    return value
