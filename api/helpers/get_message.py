from api.constants import MESSAGE_CONFIG


def get_message(m_type, subtitle, path=None):
    default = {"title": "Título", "icon": "tabler-info-small",
               "user_id": None, "roles": None}
    config = MESSAGE_CONFIG.get(m_type, default)
    return {
        "title": config["title"],
        "icon": config["icon"],
        "subtitle": subtitle,
        "is_seen": False,
        "user_id": config["user_id"],
        "roles": config["roles"],
        "path": path
    }
