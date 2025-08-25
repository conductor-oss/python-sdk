from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field

from conductor.asyncio_client.http.models import PromptTemplateTestRequest


class PromptTemplateTestRequestAdapter(PromptTemplateTestRequest):
    prompt_variables: Optional[Dict[str, Any]] = Field(
        default=None, alias="promptVariables"
    )
