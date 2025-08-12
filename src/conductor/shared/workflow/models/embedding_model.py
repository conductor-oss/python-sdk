from pydantic import BaseModel, Field


class EmbeddingModel(BaseModel):
    provider: str = Field(..., alias="embeddingModelProvider")
    model: str = Field(..., alias="embeddingModel")

    class Config:
        allow_population_by_field_name = True
