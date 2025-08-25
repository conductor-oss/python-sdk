from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., alias="role")
    message: str = Field(..., alias="message")

    class Config:
        validate_by_name = True
