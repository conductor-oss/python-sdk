from conductor.client.http.models.tag_object import TagObject


class RateLimitTag(TagObject):
    def __init__(self, key: str, value: int) -> None:
        super().__init__(key=key, type="RATE_LIMIT", value=value)
