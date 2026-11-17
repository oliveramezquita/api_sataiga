from django.http import JsonResponse


def ok(data, status=200):
    """Respuesta exitosa. `data` se serializa tal cual (dict)."""
    return JsonResponse(data, status=status, safe=False)


def fail(message, code=None, status=400):
    """Respuesta de error con mensaje y, opcionalmente, un `code` para la app."""
    payload = {"message": message}
    if code:
        payload["code"] = code
    return JsonResponse(payload, status=status)
