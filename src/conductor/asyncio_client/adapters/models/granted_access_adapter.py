from __future__ import annotations

from typing import Any, Dict, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import GrantedAccess


class GrantedAccessAdapter(GrantedAccess):
    target: Optional["TargetRefAdapter"] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of GrantedAccess from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        from conductor.asyncio_client.adapters.models.target_ref_adapter import (
            TargetRefAdapter,
        )

        _obj = cls.model_validate(
            {
                "access": obj.get("access"),
                "tag": obj.get("tag"),
                "target": (
                    TargetRefAdapter.from_dict(obj["target"])
                    if obj.get("target") is not None
                    else None
                ),
            }
        )
        return _obj
