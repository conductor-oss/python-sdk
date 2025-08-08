from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.adapters.models.group_adapter import GroupAdapter
from conductor.asyncio_client.adapters.models.role_adapter import RoleAdapter
from conductor.asyncio_client.http.models import ConductorUser


class ConductorUserAdapter(ConductorUser):
    groups: Optional[List[GroupAdapter]] = None
    roles: Optional[List[RoleAdapter]] = None
