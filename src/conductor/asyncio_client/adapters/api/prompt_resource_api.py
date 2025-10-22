from typing import List

from conductor.asyncio_client.http.api import PromptResourceApi
from conductor.asyncio_client.adapters.models.message_template_adapter import (
    MessageTemplateAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter


class PromptResourceApiAdapter(PromptResourceApi):
    async def get_message_template(self, *args, **kwargs) -> MessageTemplateAdapter:
        return await super().get_message_template(*args, **kwargs)

    async def get_message_templates(self, *args, **kwargs) -> List[MessageTemplateAdapter]:
        return await super().get_message_templates(*args, **kwargs)

    async def create_message_templates(
        self, body: List[MessageTemplateAdapter], *args, **kwargs
    ) -> None:
        return await super().create_message_templates(body, *args, **kwargs)

    async def put_tag_for_prompt_template(
        self, name, body: List[TagAdapter], *args, **kwargs
    ) -> None:
        return await super().put_tag_for_prompt_template(name, body, *args, **kwargs)

    async def get_tags_for_prompt_template(self, *args, **kwargs) -> List[TagAdapter]:
        return await super().get_tags_for_prompt_template(*args, **kwargs)

    async def delete_tag_for_prompt_template(
        self, name, body: List[TagAdapter], *args, **kwargs
    ) -> None:
        return await super().delete_tag_for_prompt_template(name, body, *args, **kwargs)
