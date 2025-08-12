from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., alias="role")
    message: str = Field(..., alias="message")

    class Config:
        allow_population_by_field_name = True
