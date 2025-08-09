from __future__ import annotations

from typing import List, Optional

from conductor.asyncio_client.adapters.models.permission_adapter import (
    PermissionAdapter,
)
from conductor.asyncio_client.http.models import Role


class RoleAdapter(Role):
    permissions: Optional[List[PermissionAdapter]] = None
