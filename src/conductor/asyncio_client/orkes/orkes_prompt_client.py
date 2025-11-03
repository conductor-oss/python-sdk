from __future__ import annotations

from typing import List, Optional

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.adapters.models.message_template_adapter import (
    MessageTemplateAdapter,
)
from conductor.asyncio_client.adapters.models.prompt_template_test_request_adapter import (
    PromptTemplateTestRequestAdapter,
)
from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.orkes.orkes_base_client import OrkesBaseClient
from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated


class OrkesPromptClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Message Template Operations
    async def save_message_template(
        self, name: str, description: str, body: str, models: Optional[List[str]] = None, **kwargs
    ) -> None:
        """Create or update a message template"""
        await self._prompt_api.save_message_template(
            name, description, body, models=models, **kwargs
        )

    async def get_message_template(self, name: str, **kwargs) -> MessageTemplateAdapter:
        """Get a message template by name"""
        return await self._prompt_api.get_message_template(name, **kwargs)

    async def get_message_templates(self, **kwargs) -> List[MessageTemplateAdapter]:
        """Get all message templates"""
        return await self._prompt_api.get_message_templates(**kwargs)

    async def delete_message_template(self, name: str, **kwargs) -> None:
        """Delete a message template"""
        await self._prompt_api.delete_message_template(name, **kwargs)

    async def create_message_templates(
        self, message_templates: List[MessageTemplateAdapter], **kwargs
    ) -> None:
        """Create multiple message templates in bulk"""
        await self._prompt_api.create_message_templates(
            message_template=message_templates, **kwargs
        )

    # Template Testing
    async def test_message_template(
        self, prompt_template_test_request: PromptTemplateTestRequestAdapter, **kwargs
    ) -> str:
        """Test a prompt template with provided inputs"""
        return await self._prompt_api.test_message_template(prompt_template_test_request, **kwargs)

    # Tag Management for Prompt Templates
    @deprecated(
        "put_tag_for_prompt_template is deprecated; use update_tag_for_prompt_template instead"
    )
    @typing_deprecated(
        "put_tag_for_prompt_template is deprecated; use update_tag_for_prompt_template instead"
    )
    async def put_tag_for_prompt_template(
        self, name: str, tags: List[TagAdapter], **kwargs
    ) -> None:
        """Add tags to a prompt template"""
        await self._prompt_api.put_tag_for_prompt_template(name, tags, **kwargs)

    async def get_tags_for_prompt_template(self, name: str, **kwargs) -> List[TagAdapter]:
        """Get tags associated with a prompt template"""
        return await self._prompt_api.get_tags_for_prompt_template(name=name, **kwargs)

    async def update_tag_for_prompt_template(
        self, prompt_name: str, tags: List[TagAdapter]
    ) -> None:
        await self._prompt_api.put_tag_for_prompt_template(name=prompt_name, tag=tags)

    async def delete_tag_for_prompt_template(
        self, name: str, tags: List[TagAdapter], **kwargs
    ) -> None:
        """Delete tags from a prompt template"""
        await self._prompt_api.delete_tag_for_prompt_template(name=name, tag=tags, **kwargs)

    # Convenience Methods
    async def create_simple_template(
        self, name: str, description: str, template_body: str, **kwargs
    ) -> None:
        """Create a simple message template with basic parameters"""
        await self.save_message_template(name, description, template_body, **kwargs)

    async def update_template(
        self,
        name: str,
        description: str,
        template_body: str,
        models: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """Update an existing message template (alias for save_message_template)"""
        await self.save_message_template(name, description, template_body, models, **kwargs)

    async def template_exists(self, name: str, **kwargs) -> bool:
        """Check if a message template exists"""
        try:
            await self.get_message_template(name, **kwargs)
            return True
        except Exception:
            return False

    async def get_templates_by_tag(
        self, tag_key: str, tag_value: str, **kwargs
    ) -> List[MessageTemplateAdapter]:
        """Get all templates that have a specific tag (requires filtering on client side)"""
        all_templates = await self.get_message_templates(**kwargs)
        matching_templates = []

        for template in all_templates:
            if not template.name:
                continue
            try:
                tags = await self.get_tags_for_prompt_template(template.name)
                if any(tag.key == tag_key and tag.value == tag_value for tag in tags):
                    matching_templates.append(template)
            except Exception:
                continue

        return matching_templates

    async def clone_template(
        self, source_name: str, target_name: str, new_description: Optional[str] = None, **kwargs
    ) -> None:
        """Clone an existing template with a new name"""
        source_template = await self.get_message_template(source_name, **kwargs)
        description = new_description or f"Clone of {source_template.description}"

        await self.save_message_template(
            target_name,
            description,
            source_template.template or "",
            models=(source_template.models if hasattr(source_template, "models") else None),
            **kwargs,
        )

    async def bulk_delete_templates(self, template_names: List[str], **kwargs) -> None:
        """Delete multiple templates in bulk"""
        for name in template_names:
            try:
                await self.delete_message_template(name, **kwargs)
            except Exception:  # noqa: PERF203
                continue

    # Legacy compatibility methods (aliasing new method names to match the original draft)
    async def save_prompt(
        self, name: str, description: str, prompt_template: str, **kwargs
    ) -> None:
        """Legacy method: Create or update a message template"""
        await self.save_message_template(
            name=name, description=description, body=prompt_template, **kwargs
        )

    async def get_prompt(self, name: str, **kwargs) -> MessageTemplateAdapter:
        """Legacy method: Get a message template by name"""
        return await self.get_message_template(name=name, **kwargs)

    async def get_prompts(self, **kwargs) -> List[MessageTemplateAdapter]:
        return await self._prompt_api.get_message_templates(**kwargs)

    async def delete_prompt(self, name: str, **kwargs) -> None:
        """Legacy method: Delete a message template"""
        await self.delete_message_template(name=name, **kwargs)

    async def list_prompts(self, **kwargs) -> List[MessageTemplateAdapter]:
        """Legacy method: Get all message templates"""
        return await self.get_message_templates(**kwargs)

    # Template Management Utilities
    async def get_template_count(self, **kwargs) -> int:
        """Get the total number of message templates"""
        templates = await self.get_message_templates(**kwargs)
        return len(templates)

    async def search_templates_by_name(
        self, name_pattern: str, **kwargs
    ) -> List[MessageTemplateAdapter]:
        """Search templates by name pattern (case-insensitive)"""
        all_templates = await self.get_message_templates(**kwargs)
        return [
            template
            for template in all_templates
            if template.name and name_pattern.lower() in template.name.lower()
        ]

    async def get_templates_with_model(
        self, model_name: str, **kwargs
    ) -> List[MessageTemplateAdapter]:
        """Get templates that use a specific AI model"""
        all_templates = await self.get_message_templates(**kwargs)
        matching_templates = []

        matching_templates = [
            template
            for template in all_templates
            if hasattr(template, "models") and template.models and model_name in template.models
        ]

        return matching_templates

    async def test_prompt(
        self,
        prompt_text: str,
        variables: dict,
        ai_integration: str,
        text_complete_model: str,
        temperature: float = 0.1,
        top_p: float = 0.9,
        stop_words: Optional[List[str]] = None,
        **kwargs,
    ) -> str:
        request = PromptTemplateTestRequestAdapter(
            prompt=prompt_text,
            llm_provider=ai_integration,
            model=text_complete_model,
            prompt_variables=variables,
            temperature=temperature,
            stop_words=stop_words,
            top_p=top_p,
        )
        return await self._prompt_api.test_message_template(
            prompt_template_test_request=request, **kwargs
        )
