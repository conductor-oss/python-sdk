from enum import Enum


class TargetType(str, Enum):
    WORKFLOW_DEF = ("WORKFLOW_DEF",)
    TASK_DEF = ("TASK_DEF",)
    APPLICATION = ("APPLICATION",)
    USER = ("USER",)
    SECRET = ("SECRET",)
    SECRET_NAME = ("SECRET_NAME",)
    TAG = ("TAG",)
    DOMAIN = "DOMAIN"
