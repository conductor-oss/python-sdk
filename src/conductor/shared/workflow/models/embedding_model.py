from pydantic import BaseModel, Field


class EmbeddingModel(BaseModel):
    provider: str = Field(..., alias="embeddingModelProvider")
    model: str = Field(..., alias="embeddingModel")

    class Config:
        validate_by_name = True
