from typing import Any, Dict

from pydantic import BaseModel, Field


class Prompt(BaseModel):
    name: str = Field(..., alias="promptName")
    variables: Dict[str, Any] = Field(..., alias="promptVariables")

    class Config:
        allow_population_by_field_name = True
