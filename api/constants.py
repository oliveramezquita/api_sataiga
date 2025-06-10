from dateutil.relativedelta import relativedelta


DEFAULT_PAGE_SIZE = 10
USER_STATUS = (
    (0, 'pending'),
    (1, 'active'),
    (2, 'inactive'),
    (3, 'deleted'),
)

REFRESH_RATES = {
    'Día': relativedelta(days=1),
    'Semana': relativedelta(weeks=1),
    'Quincena': relativedelta(days=15),
    'Mes': relativedelta(months=1),
}

MESSAGE_CONFIG = {
    "refresh_rates": {
        "title": "Actualización de precios en los materiales",
        "icon": "tabler-refresh-alert",
        "user_id": None,
        "roles": ['super', 'admin', 'ceo', 'buyer'],
    },
}

OD_STATUS = {
    'COCINA': {
        'Material Listo': 0,
        'Corte Blanco': 0,
        'Corte Color': 0,
        'Enchape': 0,
        'Armado': 0,
        'Embarque': 0,
        'total': 0,
    },
    'CLOSET': {
        'Material Listo': 0,
        'Corte Color': 0,
        'Enchape': 0,
        'Armado': 0,
        'Embarque': 0,
        'total': 0,
    },
    'PUERTAS': {
        'Material Listo': 0,
        'Corte Color': 0,
        'Enchape': 0,
        'Armado': 0,
        'Embarque': 0,
        'total': 0,
    },
    'M. DE B.': {
        'Material Listo': 0,
        'Corte Color': 0,
        'Enchape': 0,
        'Armado': 0,
        'Embarque': 0,
        'total': 0,
    },
    'WALDRAS': {
        'Material Listo': 0,
        'Corte': 0,
        'Entintado': 0,
        'Embarque': 0,
        'total': 0,
    },
    'INSTALACIÓN': {
        'Cocina': 0,
        'Granito': 0,
        'Closets': 0,
        'Vestidor': 0,
        'Mueble de Baño': 0,
        'Puertas Int': 0,
        'Waldras': 0,
        'Vobo': 0,
        'total': 0,
    },
    'total': 0,
}

FIXED_PRESENTATIONS = {
    "PAR": 2,
    "DOCENA": 12,
    "MEDIA DOCENA": 6,
    "DECENA": 10,
    "CENTENA": 100,
    "CENTENAR": 100,
    "MILLAR": 1000,
    "HOJA": 1,
    "TRAMO": 1,
    "BOBINA": 1,
    "PZS": 1,
}
