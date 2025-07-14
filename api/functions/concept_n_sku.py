def generate_concept_and_sku(data):
    """
    Generate concept and sku strings from a given dictionary.

    Args:
        data (dict): A dictionary with keys:
            - name
            - division
            - espec1
            - espec2
            - espec3
            - espec4
            - espec5

    Returns:
        dict: A dictionary with keys:
            - concept (str)
            - sku (str)
    """

    def is_valid(value):
        not_valid = ['', 'None']
        return value is not None and str(value).strip() not in not_valid

    # --- Generate concept ---
    concept_parts = [
        data.get("name"),
        data.get("espec1"),
        data.get("espec2"),
        data.get("espec3"),
        data.get("espec4"),
        data.get("espec5")
    ]
    concept = " ".join(str(part).strip()
                       for part in concept_parts if is_valid(part)).upper()

    division = data.get("division", "")
    name = data.get("name", "")

    if not is_valid(division) or not is_valid(name):
        raise ValueError(
            "Both 'division' and 'name' are required for SKU generation.")

    sku_parts = [division[:3], name[:3]]

    for key in ["espec1", "espec2"]:
        value = data.get(key)
        if is_valid(value):
            sku_parts.append(str(value).strip()[:3])

    for key in ["espec3", "espec4"]:
        value = data.get(key)
        if is_valid(value):
            sku_parts.append(str(value).strip()[:15])

    sku = "-".join(part.upper() for part in sku_parts if is_valid(part))

    return concept, sku
