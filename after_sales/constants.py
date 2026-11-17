"""
Constantes del flujo de autenticación de la app móvil de postventa.

Los valores numéricos de estatus de cuenta se toman de
`after_sales/models/auth.py` (fuente autoritativa), NO del catálogo de
CLAUDE.md que usa la numeración inversa. Ver el resumen de la feature:

    0 -> Pending activation
    1 -> Active
    2 -> Locked      (manual, lo gestiona un administrador)
    3 -> Disabled    (automático, al exceder intentos fallidos de login)
"""
from after_sales.models import Auth

STATUS_PENDING = Auth.STATUS_PENDING      # 0
STATUS_ACTIVE = Auth.STATUS_ACTIVE        # 1
STATUS_LOCKED = Auth.STATUS_LOCKED        # 2
STATUS_DISABLED = Auth.STATUS_DISABLED    # 3

# Estatus al que se lleva una cuenta cuando se exceden los intentos fallidos.
LOCKOUT_STATUS = STATUS_DISABLED

# Ruta que la app debe tomar según el estatus devuelto por /auth/identify/.
STATUS_ROUTE = {
    STATUS_PENDING: "first_access",
    STATUS_ACTIVE: "login",
    STATUS_LOCKED: "locked",
    STATUS_DISABLED: "disabled",
}

# Colecciones MongoDB usadas por esta app.
COLLECTION_AUTH = "auth"
COLLECTION_VERIFICATION = "auth_verification"
COLLECTION_DEVICE = "auth_device"
COLLECTION_TOKEN_BLACKLIST = "auth_token_blacklist"

# Tipos de verificación (coinciden con AuthVerification.verification_type).
VERIFICATION_ACTIVATION = "activation"
VERIFICATION_LOGIN = "login"
VERIFICATION_PASSWORD_RESET = "password_reset"

# Propósitos aceptados en /auth/verification/send/ y confirm/.
PURPOSE_TO_VERIFICATION_TYPE = {
    "activation": VERIFICATION_ACTIVATION,
    "first_access": VERIFICATION_ACTIVATION,
    "login": VERIFICATION_LOGIN,
    "device": VERIFICATION_LOGIN,
}
