from datetime import datetime

import locale

locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")  # Set Spanish locale


def time_ago(dt):
    now = datetime.now()
    diff = now - dt

    if diff.total_seconds() < 60:
        return "Ahora"
    elif diff.total_seconds() < 3600:
        return f"{int(diff.total_seconds() / 60)} minutos atrás"
    elif diff.total_seconds() < 86400:
        return f"{int(diff.total_seconds() / 3600)} horas atrás"
    elif diff.days == 0:
        return "Hoy"
    elif diff.days == 1:
        return "Ayer"
    elif diff.days < 30:
        return f"Hace {diff.days} días"
    else:
        return dt.strftime("%d de %B")
