from typing import Any, Dict

from pydantic import BaseModel, Field

from conductor.shared.http.enums import AccessKeyStatus


class AccessKeyAdapter(BaseModel):
    id: str
    status: AccessKeyStatus
    created_at: int = Field(alias="createdAt")

    @classmethod
    def from_dict(cls, obj: Dict[str, Any]) -> "AccessKeyAdapter":
        _obj = cls.model_validate(
            {
                "id": obj.get("id"),
                "status": obj.get("status"),
                "createdAt": obj.get("createdAt"),
            }
        )
        return _obj
