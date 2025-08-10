from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.granted_access_adapter import (
    GrantedAccessAdapter,
)
from conductor.asyncio_client.http.models import GrantedAccessResponse
from typing_extensions import Self


class GrantedAccessResponseAdapter(GrantedAccessResponse):
    granted_access: Optional[List[GrantedAccessAdapter]] = Field(
        default=None, alias="grantedAccess"
    )

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of GrantedAccessResponse from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "grantedAccess": [GrantedAccessAdapter.from_dict(_item) for _item in obj["grantedAccess"]] if obj.get("grantedAccess") is not None else None
        })
        return _obj
