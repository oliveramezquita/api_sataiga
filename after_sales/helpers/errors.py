class AuthError(Exception):
    """
    Error de negocio del flujo de autenticación.

    El decorador `endpoint` lo traduce a una respuesta JSON con
    `status_code` y un `code` legible por la app móvil.
    """

    def __init__(self, message, code=None, status_code=400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
