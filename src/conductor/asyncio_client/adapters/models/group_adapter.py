from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import field_validator
from typing_extensions import Self

from conductor.asyncio_client.http.models import Group


class GroupAdapter(Group):
    roles: Optional[List["RoleAdapter"]] = None

    @field_validator("default_access")
    def default_access_validate_enum(cls, value):
        return value

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of Group from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "defaultAccess": obj.get("defaultAccess"),
                "description": obj.get("description"),
                "id": obj.get("id"),
                "roles": (
                    [RoleAdapter.from_dict(_item) for _item in obj["roles"]]
                    if obj.get("roles") is not None
                    else None
                ),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.role_adapter import RoleAdapter  # noqa: E402

GroupAdapter.model_rebuild(raise_errors=False)
