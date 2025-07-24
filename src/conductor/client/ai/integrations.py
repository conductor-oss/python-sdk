from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Optional

class IntegrationConfig(ABC):
    @abstractmethod
    def to_dict(self) -> dict:
        pass


class WeaviateConfig(IntegrationConfig):

    def __init__(self, api_key: str, endpoint: str, classname: str) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.classname = classname

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key,
            "endpoint": self.endpoint
        }


class OpenAIConfig(IntegrationConfig):

    def __init__(self, api_key: Optional[str] = None) -> None:
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        self.api_key = api_key

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key
        }


class AzureOpenAIConfig(IntegrationConfig):

    def __init__(self, api_key: str, endpoint: str) -> None:
        self.api_key = api_key
        self.endpoint = endpoint

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key,
            "endpoint": self.endpoint
        }


class PineconeConfig(IntegrationConfig):

    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None, environment: Optional[str] = None, project_name: Optional[str] = None) -> None:
        if api_key is None:
            self.api_key = os.getenv("PINECONE_API_KEY")
        else:
            self.api_key = api_key

        if endpoint is None:
            self.endpoint = os.getenv("PINECONE_ENDPOINT")
        else:
            self.endpoint = endpoint

        if environment is None:
            self.environment = os.getenv("PINECONE_ENV")
        else:
            self.environment = environment

        if project_name is None:
            self.project_name = os.getenv("PINECONE_PROJECT")
        else:
            self.project_name = project_name

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key,
            "endpoint": self.endpoint,
            "projectName": self.project_name,
            "environment": self.environment
        }
