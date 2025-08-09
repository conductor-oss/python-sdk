from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from conductor.asyncio_client.adapters.models.granted_access_adapter import (
    GrantedAccessAdapter,
)
from conductor.asyncio_client.http.models import GrantedAccessResponse


class GrantedAccessResponseAdapter(GrantedAccessResponse):
    granted_access: Optional[List[GrantedAccessAdapter]] = Field(
        default=None, alias="grantedAccess"
    )
