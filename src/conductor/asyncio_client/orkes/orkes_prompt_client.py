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


class OrkesPromptClient(OrkesBaseClient):
    def __init__(self, configuration: Configuration, api_client: ApiClient):
        super().__init__(configuration, api_client)

    # Message Template Operations
    async def save_message_template(
        self, name: str, description: str, body: str, models: Optional[List[str]] = None
    ) -> None:
        """Create or update a message template"""
        await self._prompt_api.save_message_template(name, description, body, models=models)

    async def get_message_template(self, name: str) -> MessageTemplateAdapter:
        """Get a message template by name"""
        return await self._prompt_api.get_message_template(name)

    async def get_message_templates(self) -> List[MessageTemplateAdapter]:
        """Get all message templates"""
        return await self._prompt_api.get_message_templates()

    async def delete_message_template(self, name: str) -> None:
        """Delete a message template"""
        await self._prompt_api.delete_message_template(name)

    async def create_message_templates(
        self, message_templates: List[MessageTemplateAdapter]
    ) -> None:
        """Create multiple message templates in bulk"""
        await self._prompt_api.create_message_templates(message_templates)

    # Template Testing
    async def test_message_template(
        self, prompt_template_test_request: PromptTemplateTestRequestAdapter
    ) -> str:
        """Test a prompt template with provided inputs"""
        return await self._prompt_api.test_message_template(prompt_template_test_request)

    # Tag Management for Prompt Templates
    async def put_tag_for_prompt_template(self, name: str, tags: List[TagAdapter]) -> None:
        """Add tags to a prompt template"""
        await self._prompt_api.put_tag_for_prompt_template(name, tags)

    async def get_tags_for_prompt_template(self, name: str) -> List[TagAdapter]:
        """Get tags associated with a prompt template"""
        return await self._prompt_api.get_tags_for_prompt_template(name)

    async def delete_tag_for_prompt_template(self, name: str, tags: List[TagAdapter]) -> None:
        """Delete tags from a prompt template"""
        await self._prompt_api.delete_tag_for_prompt_template(name, tags)

    # Convenience Methods
    async def create_simple_template(self, name: str, description: str, template_body: str) -> None:
        """Create a simple message template with basic parameters"""
        await self.save_message_template(name, description, template_body)

    async def update_template(
        self,
        name: str,
        description: str,
        template_body: str,
        models: Optional[List[str]] = None,
    ) -> None:
        """Update an existing message template (alias for save_message_template)"""
        await self.save_message_template(name, description, template_body, models)

    async def template_exists(self, name: str) -> bool:
        """Check if a message template exists"""
        try:
            await self.get_message_template(name)
            return True
        except Exception:
            return False

    async def get_templates_by_tag(
        self, tag_key: str, tag_value: str
    ) -> List[MessageTemplateAdapter]:
        """Get all templates that have a specific tag (requires filtering on client side)"""
        all_templates = await self.get_message_templates()
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
        self, source_name: str, target_name: str, new_description: Optional[str] = None
    ) -> None:
        """Clone an existing template with a new name"""
        source_template = await self.get_message_template(source_name)
        description = new_description or f"Clone of {source_template.description}"

        await self.save_message_template(
            target_name,
            description,
            source_template.template or "",
            models=(source_template.models if hasattr(source_template, "models") else None),
        )

    async def bulk_delete_templates(self, template_names: List[str]) -> None:
        """Delete multiple templates in bulk"""
        for name in template_names:
            try:
                await self.delete_message_template(name)
            except Exception:  # noqa: PERF203
                continue

    # Legacy compatibility methods (aliasing new method names to match the original draft)
    async def save_prompt(self, name: str, description: str, prompt_template: str) -> None:
        """Legacy method: Create or update a message template"""
        await self.save_message_template(name, description, prompt_template)

    async def get_prompt(self, name: str) -> MessageTemplateAdapter:
        """Legacy method: Get a message template by name"""
        return await self.get_message_template(name)

    async def delete_prompt(self, name: str) -> None:
        """Legacy method: Delete a message template"""
        await self.delete_message_template(name)

    async def list_prompts(self) -> List[MessageTemplateAdapter]:
        """Legacy method: Get all message templates"""
        return await self.get_message_templates()

    # Template Management Utilities
    async def get_template_count(self) -> int:
        """Get the total number of message templates"""
        templates = await self.get_message_templates()
        return len(templates)

    async def search_templates_by_name(self, name_pattern: str) -> List[MessageTemplateAdapter]:
        """Search templates by name pattern (case-insensitive)"""
        all_templates = await self.get_message_templates()
        return [
            template
            for template in all_templates
            if template.name and name_pattern.lower() in template.name.lower()
        ]

    async def get_templates_with_model(self, model_name: str) -> List[MessageTemplateAdapter]:
        """Get templates that use a specific AI model"""
        all_templates = await self.get_message_templates()
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
        return await self._prompt_api.test_message_template(request)
