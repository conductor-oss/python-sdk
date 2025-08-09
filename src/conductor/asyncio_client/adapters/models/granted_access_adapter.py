from __future__ import annotations

from typing import Optional

from conductor.asyncio_client.adapters.models.target_ref_adapter import TargetRefAdapter
from conductor.asyncio_client.http.models import GrantedAccess


class GrantedAccessAdapter(GrantedAccess):
    target: Optional[TargetRefAdapter] = None
