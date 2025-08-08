from __future__ import annotations

from typing import Optional, List

from conductor.asyncio_client.http.models import Role
from conductor.asyncio_client.adapters.models.permission_adapter import PermissionAdapter


class RoleAdapter(Role):
    permissions: Optional[List[PermissionAdapter]] = None
