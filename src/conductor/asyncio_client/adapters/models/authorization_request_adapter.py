from __future__ import annotations

from typing import Any, Dict, Optional

from typing_extensions import Self

from conductor.asyncio_client.adapters.models.subject_ref_adapter import (
    SubjectRefAdapter,
)
from conductor.asyncio_client.adapters.models.target_ref_adapter import TargetRefAdapter
from conductor.asyncio_client.http.models import AuthorizationRequest


class AuthorizationRequestAdapter(AuthorizationRequest):
    subject: SubjectRefAdapter
    target: TargetRefAdapter

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of AuthorizationRequest from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "access": obj.get("access"),
                "subject": (
                    SubjectRefAdapter.from_dict(obj["subject"])
                    if obj.get("subject") is not None
                    else None
                ),
                "target": (
                    TargetRefAdapter.from_dict(obj["target"])
                    if obj.get("target") is not None
                    else None
                ),
            }
        )
        return _obj
