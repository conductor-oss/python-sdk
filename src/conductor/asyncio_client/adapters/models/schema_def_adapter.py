from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from conductor.asyncio_client.http.models import SchemaDef


class SchemaType(str, Enum):
    JSON = ("JSON",)
    AVRO = ("AVRO",)
    PROTOBUF = "PROTOBUF"

    def __str__(self) -> str:
        return self.name.__str__()


class SchemaDefAdapter(SchemaDef):
    data: Optional[Dict[str, Any]] = None
