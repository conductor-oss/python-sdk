from __future__ import annotations

from typing import Any, Dict, List, Optional

from typing_extensions import Self

from conductor.asyncio_client.http.models import ConductorUser


class ConductorUserAdapter(ConductorUser):
    groups: Optional[List["GroupAdapter"]] = None
    roles: Optional[List["RoleAdapter"]] = None

    @classmethod
    def from_dict(cls, obj: Optional[Dict[str, Any]]) -> Optional[Self]:
        """Create an instance of ConductorUser from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate(
            {
                "applicationUser": obj.get("applicationUser"),
                "encryptedId": obj.get("encryptedId"),
                "encryptedIdDisplayValue": obj.get("encryptedIdDisplayValue"),
                "groups": (
                    [GroupAdapter.from_dict(_item) for _item in obj["groups"]]
                    if obj.get("groups") is not None
                    else None
                ),
                "id": obj.get("id"),
                "name": obj.get("name"),
                "orkesWorkersApp": obj.get("orkesWorkersApp"),
                "roles": (
                    [RoleAdapter.from_dict(_item) for _item in obj["roles"]]
                    if obj.get("roles") is not None
                    else None
                ),
                "uuid": obj.get("uuid"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter  # noqa: E402
from conductor.asyncio_client.adapters.models.role_adapter import RoleAdapter  # noqa: E402

ConductorUserAdapter.model_rebuild(raise_errors=False)
