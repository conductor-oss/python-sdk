from enum import Enum


class SubjectType(str, Enum):
    USER = ("USER",)
    ROLE = ("ROLE",)
    GROUP = ("GROUP",)
    TAG = "TAG"
