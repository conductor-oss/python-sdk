from enum import Enum
from conductor.client.http.models.tag import Tag


class TypeEnum(str, Enum):
    METADATA = "METADATA"
    RATE_LIMIT = "RATE_LIMIT"


class TagAdapter(Tag):
    pass
