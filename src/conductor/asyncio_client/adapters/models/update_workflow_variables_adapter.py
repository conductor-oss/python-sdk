from __future__ import annotations

from typing import Optional, Dict, Any
from conductor.asyncio_client.http.models import UpdateWorkflowVariables


class UpdateWorkflowVariablesAdapter(UpdateWorkflowVariables):
    variables: Optional[Dict[str, Dict[str, Any]]] = None
