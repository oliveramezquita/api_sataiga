import re


def email_validation(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if not re.fullmatch(regex, email):
        return False
    return True


def objectid_validation(object_id):
    if isinstance(object_id, str) and len(object_id) == 24:
        return True
    return False
