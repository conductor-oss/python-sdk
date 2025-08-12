from typing import Any, Dict

from pydantic import BaseModel, Field


class Prompt(BaseModel):
    name: str = Field(..., alias="promptName")
    variables: Dict[str, Any] = Field(..., alias="promptVariables")

    class Config:
        validate_by_name = True
