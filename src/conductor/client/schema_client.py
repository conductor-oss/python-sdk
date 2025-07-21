from __future__ import absolute_import

import re  # noqa: F401
from abc import ABC, abstractmethod
from typing import List

# python 2 and python 3 compatibility library

from conductor.client.http.models.schema_def import SchemaDef


class SchemaClient(ABC):

    @abstractmethod
    def register_schema(self, schema: SchemaDef) -> None:
        """
        Register a new schema.
        """

    @abstractmethod
    def get_schema(self, schema_name: str, version: int) -> SchemaDef:
        """
        Retrieve a schema by its name and version.
        """

    @abstractmethod
    def get_all_schemas(self) -> List[SchemaDef]:
        """
        Retrieve all schemas.
        """

    @abstractmethod
    def delete_schema(self, schema_name: str, version: int) -> None:
        """
        Delete a schema by its name and version.
        """

    @abstractmethod
    def delete_schema_by_name(self, schema_name: str) -> None:
        """
        Delete all the versions of a schema by its name
        """
