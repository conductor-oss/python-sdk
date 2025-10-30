from typing import Dict, Any

from pydantic import BaseModel


class CreatedAccessKeyAdapter(BaseModel):
    id: str
    secret: str

    @classmethod
    def from_dict(cls, obj: Dict[str, Any]) -> "CreatedAccessKeyAdapter":
        return cls(
            id=obj["id"],
            secret=obj["secret"],
        )
