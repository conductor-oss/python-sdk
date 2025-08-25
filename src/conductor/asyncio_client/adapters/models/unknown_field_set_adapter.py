from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field
from typing_extensions import Self

from conductor.asyncio_client.http.models import UnknownFieldSet


class UnknownFieldSetAdapter(UnknownFieldSet):
    default_instance_for_type: Optional["UnknownFieldSetAdapter"] = Field(
        default=None, alias="defaultInstanceForType"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of UnknownFieldSet from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "defaultInstanceForType": (
                    UnknownFieldSetAdapter.from_dict(obj["defaultInstanceForType"])
                    if obj.get("defaultInstanceForType") is not None
                    else None
                ),
                "initialized": obj.get("initialized"),
                "parserForType": obj.get("parserForType"),
                "serializedSize": obj.get("serializedSize"),
                "serializedSizeAsMessageSet": obj.get("serializedSizeAsMessageSet"),
            }
        )
        return _obj
