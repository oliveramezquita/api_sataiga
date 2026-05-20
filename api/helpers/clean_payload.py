def clean_payload(data):
    """
    Limpia strings recursivamente:
    - " Probando       " -> "Probando"
    - "   " -> None
    - Mantiene listas, dicts y otros tipos.
    """
    if isinstance(data, dict):
        return {key: clean_payload(value) for key, value in data.items()}

    if isinstance(data, list):
        return [clean_payload(item) for item in data]

    if isinstance(data, str):
        value = data.strip()
        return value if value else None

    return data
