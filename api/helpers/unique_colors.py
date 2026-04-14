from typing import Any, Dict, List


def unique_colors(data: List[Dict[str, Any]]) -> List[str]:
    unique = {
        part.strip()
        for item in data
        for part in item.get("name", "").split("/")
        if part.strip()
    }
    return sorted(unique)
