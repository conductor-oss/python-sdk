from __future__ import annotations

from pydantic import Field
from typing import ClassVar, List, Optional, Any, Dict

from typing_extensions import Self

from conductor.asyncio_client.http.models import BulkResponse


class BulkResponseAdapter(BulkResponse):
    message: str = Field(default="Bulk Request has been processed.")
    __properties: ClassVar[List[str]] = ["bulkErrorResults", "bulkSuccessfulResults", "message"]

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of BulkResponse from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "bulkErrorResults": obj.get("bulkErrorResults"),
            "bulkSuccessfulResults": obj.get("bulkSuccessfulResults"),
            "message": obj.get("message")
        })
        return _obj