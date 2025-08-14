from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import Role


class RoleAdapter(Role):
    permissions: Optional[List["PermissionAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Role from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        from conductor.asyncio_client.adapters.models.permission_adapter import (
            PermissionAdapter,
        )

        _obj = cls.model_validate(
            {
                "name": obj.get("name"),
                "permissions": (
                    [PermissionAdapter.from_dict(_item) for _item in obj["permissions"]]
                    if obj.get("permissions") is not None
                    else None
                ),
            }
        )
        return _obj
