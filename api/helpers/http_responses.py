from django.http import JsonResponse, HttpResponse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


def build_response(message, data=None):
    if data is None:
        payload = {
            'message': message
        }
    else:
        payload = {
            'message': message,
            'data': data
        }
    return JsonResponse(payload, safe=False)


def build_response_no_message(data):
    return JsonResponse(data, safe=False)


def build_response_with_pagination(paginator, page, data):
    payload = {
        "total_pages": paginator.num_pages,
        "total_elements": paginator.count,
        "last": not page.has_next(),
        "page_size": len(page),
        "page": page.number,
        "data": data
    }
    return JsonResponse(payload, safe=False)


def ok(data):
    response = build_response_no_message(data)
    response.status_code = HTTP_200_OK
    return response


def ok_paginated(paginator, page, data):
    response = build_response_with_pagination(paginator, page, data)
    response.status_code = HTTP_200_OK
    return response


def created(data):
    response = build_response_no_message(data)
    response.status_code = HTTP_201_CREATED
    return response


def not_content():
    return HttpResponse(status=HTTP_204_NO_CONTENT)


def bad_request(message, status_code=HTTP_400_BAD_REQUEST):
    response = JsonResponse([message], safe=False)
    response.status_code = status_code
    return response


def not_found(message, data=None):
    response = build_response(message, data)
    response.status_code = HTTP_404_NOT_FOUND
    return response


def error(message, data=None):
    response = build_response(message, data)
    response.status_code = HTTP_500_INTERNAL_SERVER_ERROR
    return response
