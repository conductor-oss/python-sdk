from typing import ClassVar, Dict


class EmbeddingModel(object):
    swagger_types: ClassVar[Dict[str, str]] = {"provider": "str", "model": "str"}

    attribute_map: ClassVar[Dict[str, str]] = {
        "provider": "embeddingModelProvider",
        "model": "embeddingModel",
    }

    def __init__(self, provider: str, model: str):
        self._provider = provider
        self._model = model

    @property
    def provider(self) -> str:
        return self._provider

    @provider.setter
    def provider(self, provider: str) -> None:
        self._provider = provider

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, model: str) -> None:
        self._model = model
