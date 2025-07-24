import json

from conductor.client.exceptions.api_error import APIError, APIErrorCode
from conductor.client.http.rest import ApiException

BAD_REQUEST_STATUS = 400
FORBIDDEN_STATUS = 403
NOT_FOUND_STATUS = 404
REQUEST_TIMEOUT_STATUS = 408
CONFLICT_STATUS = 409

STATUS_TO_MESSAGE_DEFAULT_MAPPING = {
    BAD_REQUEST_STATUS: "Invalid request",
    FORBIDDEN_STATUS: "Access forbidden",
    NOT_FOUND_STATUS: "Resource not found",
    REQUEST_TIMEOUT_STATUS: "Request timed out",
    CONFLICT_STATUS: "Resource exists already",
}


def api_exception_handler(function):
    def inner_function(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except ApiException as e:

            if e.status == NOT_FOUND_STATUS:
                code = APIErrorCode.NOT_FOUND
            elif e.status == FORBIDDEN_STATUS:
                code = APIErrorCode.FORBIDDEN
            elif e.status == CONFLICT_STATUS:
                code = APIErrorCode.CONFLICT
            elif e.status == BAD_REQUEST_STATUS:
                code = APIErrorCode.BAD_REQUEST
            elif e.status == REQUEST_TIMEOUT_STATUS:
                code = APIErrorCode.REQUEST_TIMEOUT
            else:
                code = APIErrorCode.UNKNOWN

            message = STATUS_TO_MESSAGE_DEFAULT_MAPPING.get(e.status, "Unknown error")

            try:
                if e.body:
                    error = json.loads(e.body)
                    message = error["message"]
            except ValueError:
                message = e.body

            finally:
                raise APIError(code, message)

    return inner_function


def for_all_methods(decorator, exclude=None):
    def decorate(cls):
        exclude_local = [] if exclude is None else exclude
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)) and attr not in exclude_local:
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate