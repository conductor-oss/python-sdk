from enum import Enum


class HttpMethod(str, Enum):
    GET = ("GET",)
    PUT = ("PUT",)
    POST = ("POST",)
    DELETE = ("DELETE",)
    HEAD = ("HEAD",)
    OPTIONS = "OPTIONS"
