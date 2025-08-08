from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.adapters.models.role_adapter import RoleAdapter
from conductor.asyncio_client.http.models import Group


class GroupAdapter(Group):
    roles: Optional[List[RoleAdapter]] = None
