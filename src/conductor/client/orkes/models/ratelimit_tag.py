from typing_extensions import Self

from conductor.client.http.models.tag_object import TagObject


class RateLimitTag(TagObject):
    def __init__(self, key: str, value: int) -> Self:
        super().__init__(key=key, type="RATE_LIMIT", value=value)
