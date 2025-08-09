from __future__ import annotations

from typing import Any, Dict, Optional

from conductor.asyncio_client.http.models import SchemaDef


class SchemaDefAdapter(SchemaDef):
    data: Optional[Dict[str, Any]] = None
