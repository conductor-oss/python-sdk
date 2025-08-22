from enum import Enum


class EvaluatorType(str, Enum):
    JAVASCRIPT = ("javascript",)
    ECMASCRIPT = ("graaljs",)
    VALUE_PARAM = "value-param"
