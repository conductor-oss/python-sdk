from typing_extensions import Self

from conductor.client.http.models.tag_object import TagObject


class MetadataTag(TagObject):
    def __init__(self, key: str, value: str) -> Self:
        super().__init__(key=key, type="METADATA", value=value)
