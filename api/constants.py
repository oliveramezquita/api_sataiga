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
    "purchase_order_generated": {
        "title": "Nueva orden de compra generada",
        "icon": "tabler-shopping-cart-plus",
        "user_id": None,
        "roles": ['super', 'admin', 'ceo', 'buyer'],
    },
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
    "PZA": 1,
}
