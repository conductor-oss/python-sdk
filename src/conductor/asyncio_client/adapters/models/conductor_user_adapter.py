from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field, StrictBool
from typing_extensions import Self

from conductor.asyncio_client.http.models import ConductorUser


class ConductorUserAdapter(ConductorUser):
    groups: Optional[List["GroupAdapter"]] = None  # type: ignore[assignment]
    roles: Optional[List["RoleAdapter"]] = None  # type: ignore[assignment]
    orkes_app: Optional[StrictBool] = Field(default=None, alias="orkesApp")
    orkes_api_gateway: Optional[StrictBool] = Field(default=None, alias="orkesApiGateway")
    contact_information: Optional[Dict[Any, str]] = Field(default=None, alias="contactInformation")

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
                "orkesApp": obj.get("orkesApp"),
                "orkesApiGateway": obj.get("orkesApiGateway"),
                "contactInformation": obj.get("contactInformation"),
            }
        )
        return _obj


from conductor.asyncio_client.adapters.models.group_adapter import (  # noqa: E402
    GroupAdapter,
)
from conductor.asyncio_client.adapters.models.role_adapter import (  # noqa: E402
    RoleAdapter,
)

ConductorUserAdapter.model_rebuild(raise_errors=False)
