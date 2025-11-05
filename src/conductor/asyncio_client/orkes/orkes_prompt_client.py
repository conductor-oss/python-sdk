from __future__ import annotations

from typing import List, Optional

from deprecated import deprecated
from typing_extensions import deprecated as typing_deprecated

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
        """Initialize the OrkesPromptClient with configuration and API client.

        Args:
            configuration: Configuration object containing server settings and authentication
            api_client: ApiClient instance for making API requests

        Example:
            ```python
            from conductor.asyncio_client.configuration.configuration import Configuration
            from conductor.asyncio_client.adapters import ApiClient

            config = Configuration(server_api_url="http://localhost:8080/api")
            api_client = ApiClient(configuration=config)
            prompt_client = OrkesPromptClient(config, api_client)
            ```
        """
        super().__init__(configuration, api_client)

    # Message Template Operations
    async def save_message_template(
        self, name: str, description: str, body: str, models: Optional[List[str]] = None, **kwargs
    ) -> None:
        """Create or update a message template.

        Message templates are reusable prompt templates for AI integrations with
        variable substitution support.

        Args:
            name: Unique name for the template
            description: Human-readable description of the template's purpose
            body: Template text with variables in ${variable} format
            models: Optional list of AI models this template is compatible with
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Create a customer service template
            await prompt_client.save_message_template(
                name="customer_greeting",
                description="Greeting template for customer service",
                body="Hello ${customer_name}, welcome to ${company}! How can I help you today?",
                models=["gpt-4", "gpt-3.5-turbo"]
            )
            ```
        """
        await self._prompt_api.save_message_template(
            name=name, description=description, body=body, models=models, **kwargs
        )

    async def get_message_template(self, name: str, **kwargs) -> MessageTemplateAdapter:
        """Get a message template by name.

        Args:
            name: Name of the template to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            MessageTemplateAdapter instance containing the template details

        Example:
            ```python
            template = await prompt_client.get_message_template("customer_greeting")
            print(f"Template: {template.template}")
            print(f"Models: {template.models}")
            ```
        """
        return await self._prompt_api.get_message_template(name=name, **kwargs)

    async def get_message_templates(self, **kwargs) -> List[MessageTemplateAdapter]:
        """Get all message templates.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MessageTemplateAdapter instances

        Example:
            ```python
            templates = await prompt_client.get_message_templates()
            for template in templates:
                print(f"Template: {template.name} - {template.description}")
            ```
        """
        return await self._prompt_api.get_message_templates(**kwargs)

    async def delete_message_template(self, name: str, **kwargs) -> None:
        """Delete a message template.

        Args:
            name: Name of the template to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await prompt_client.delete_message_template("old_template")
            ```
        """
        await self._prompt_api.delete_message_template(name=name, **kwargs)

    async def create_message_templates(
        self, message_templates: List[MessageTemplateAdapter], **kwargs
    ) -> None:
        """Create multiple message templates in bulk.

        Args:
            message_templates: List of template objects to create
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.message_template_adapter import MessageTemplateAdapter

            templates = [
                MessageTemplateAdapter(
                    name="greeting",
                    description="Greeting template",
                    template="Hello ${name}!"
                ),
                MessageTemplateAdapter(
                    name="farewell",
                    description="Farewell template",
                    template="Goodbye ${name}!"
                )
            ]
            await prompt_client.create_message_templates(templates)
            ```
        """
        await self._prompt_api.create_message_templates(
            message_template=message_templates, **kwargs
        )

    # Template Testing
    async def test_message_template(
        self, prompt_template_test_request: PromptTemplateTestRequestAdapter, **kwargs
    ) -> str:
        """Test a prompt template with provided inputs.

        Tests how a template will be rendered with specific variables and AI model settings.

        Args:
            prompt_template_test_request: Test request containing template, variables, and model config
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            String containing the rendered/tested prompt result

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.prompt_template_test_request_adapter import PromptTemplateTestRequestAdapter

            test_request = PromptTemplateTestRequestAdapter(
                prompt="Hello ${name}, you have ${count} messages",
                prompt_variables={"name": "John", "count": "5"},
                llm_provider="openai",
                model="gpt-4",
                temperature=0.7
            )
            result = await prompt_client.test_message_template(test_request)
            print(f"Rendered template: {result}")
            ```
        """
        return await self._prompt_api.test_message_template(
            prompt_template_test_request=prompt_template_test_request, **kwargs
        )

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
        """Add tags to a prompt template.

        .. deprecated::
            Use update_tag_for_prompt_template instead.

        Args:
            name: Name of the template
            tags: List of tags to add
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(key="category", value="customer-service")]
            await prompt_client.put_tag_for_prompt_template("greeting", tags)
            ```
        """
        await self._prompt_api.put_tag_for_prompt_template(name, tags, **kwargs)

    async def get_tags_for_prompt_template(self, name: str, **kwargs) -> List[TagAdapter]:
        """Get tags associated with a prompt template.

        Args:
            name: Name of the template
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of TagAdapter instances

        Example:
            ```python
            tags = await prompt_client.get_tags_for_prompt_template("customer_greeting")
            for tag in tags:
                print(f"{tag.key}: {tag.value}")
            ```
        """
        return await self._prompt_api.get_tags_for_prompt_template(name=name, **kwargs)

    async def update_tag_for_prompt_template(
        self, prompt_name: str, tags: List[TagAdapter], **kwargs
    ) -> None:
        """Update tags for a prompt template.

        Args:
            prompt_name: Name of the template
            tags: List of tags to set
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [
                TagAdapter(key="category", value="customer-service"),
                TagAdapter(key="version", value="v2")
            ]
            await prompt_client.update_tag_for_prompt_template("greeting", tags)
            ```
        """
        await self._prompt_api.put_tag_for_prompt_template(name=prompt_name, tag=tags, **kwargs)

    async def delete_tag_for_prompt_template(
        self, name: str, tags: List[TagAdapter], **kwargs
    ) -> None:
        """Delete tags from a prompt template.

        Args:
            name: Name of the template
            tags: List of tags to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.asyncio_client.adapters.models.tag_adapter import TagAdapter

            tags = [TagAdapter(key="category", value="customer-service")]
            await prompt_client.delete_tag_for_prompt_template("greeting", tags)
            ```
        """
        await self._prompt_api.delete_tag_for_prompt_template(name=name, tag=tags, **kwargs)

    # Convenience Methods
    async def create_simple_template(
        self, name: str, description: str, template_body: str, **kwargs
    ) -> None:
        """Create a simple message template with basic parameters.

        Convenience method for creating templates without specifying models.

        Args:
            name: Unique name for the template
            description: Description of the template
            template_body: Template text with variables
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await prompt_client.create_simple_template(
                "simple_greeting",
                "Basic greeting",
                "Hello ${name}!"
            )
            ```
        """
        await self.save_message_template(name, description, template_body, **kwargs)

    async def update_template(
        self,
        name: str,
        description: str,
        template_body: str,
        models: Optional[List[str]] = None,
        **kwargs,
    ) -> None:
        """Update an existing message template (alias for save_message_template).

        Args:
            name: Name of the template to update
            description: Updated description
            template_body: Updated template text
            models: Optional list of compatible AI models
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await prompt_client.update_template(
                "customer_greeting",
                "Updated greeting template",
                "Hi ${customer_name}, welcome back!",
                models=["gpt-4"]
            )
            ```
        """
        await self.save_message_template(name, description, template_body, models, **kwargs)

    async def template_exists(self, name: str, **kwargs) -> bool:
        """Check if a message template exists.

        Args:
            name: Name of the template to check
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            True if template exists, False otherwise

        Example:
            ```python
            if await prompt_client.template_exists("customer_greeting"):
                print("Template exists")
            else:
                print("Template not found")
            ```
        """
        try:
            await self.get_message_template(name, **kwargs)
            return True
        except Exception:
            return False

    async def get_templates_by_tag(
        self, tag_key: str, tag_value: str, **kwargs
    ) -> List[MessageTemplateAdapter]:
        """Get all templates that have a specific tag.

        Note: This method fetches all templates and filters client-side.

        Args:
            tag_key: Tag key to filter by
            tag_value: Tag value to filter by
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MessageTemplateAdapter instances with matching tag

        Example:
            ```python
            # Get all customer service templates
            templates = await prompt_client.get_templates_by_tag(
                "category",
                "customer-service"
            )
            ```
        """
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
        """Clone an existing template with a new name.

        Args:
            source_name: Name of the template to clone
            target_name: Name for the cloned template
            new_description: Optional description for the clone. If None, uses "Clone of {original}"
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Clone a template
            await prompt_client.clone_template(
                "customer_greeting",
                "partner_greeting",
                "Greeting template for partners"
            )
            ```
        """
        source_template = await self.get_message_template(source_name, **kwargs)
        description = new_description or f"Clone of {source_template.description}"

        await self.save_message_template(
            name=target_name,
            description=description,
            body=source_template.template or "",
            models=(source_template.models if hasattr(source_template, "models") else None),
            **kwargs,
        )

    async def bulk_delete_templates(self, template_names: List[str], **kwargs) -> None:
        """Delete multiple templates in bulk.

        Continues deleting even if some deletions fail.

        Args:
            template_names: List of template names to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            templates_to_delete = ["old_template1", "old_template2", "old_template3"]
            await prompt_client.bulk_delete_templates(templates_to_delete)
            ```
        """
        for name in template_names:
            try:
                await self.delete_message_template(name=name, **kwargs)
            except Exception:  # noqa: PERF203
                continue

    # Legacy compatibility methods (aliasing new method names to match the original draft)
    async def save_prompt(
        self, name: str, description: str, prompt_template: str, **kwargs
    ) -> None:
        """Create or update a message template (legacy alias).

        Args:
            name: Name of the template
            description: Description of the template
            prompt_template: Template text
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await prompt_client.save_prompt(
                "greeting",
                "Customer greeting",
                "Hello ${customer}!"
            )
            ```
        """
        await self.save_message_template(
            name=name, description=description, body=prompt_template, **kwargs
        )

    async def get_prompt(self, name: str, **kwargs) -> MessageTemplateAdapter:
        """Get a message template by name (legacy alias).

        Args:
            name: Name of the template
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            MessageTemplateAdapter instance

        Example:
            ```python
            prompt = await prompt_client.get_prompt("greeting")
            ```
        """
        return await self.get_message_template(name=name, **kwargs)

    async def get_prompts(self, **kwargs) -> List[MessageTemplateAdapter]:
        """Get all message templates (legacy alias).

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MessageTemplateAdapter instances

        Example:
            ```python
            prompts = await prompt_client.get_prompts()
            ```
        """
        return await self._prompt_api.get_message_templates(**kwargs)

    async def delete_prompt(self, name: str, **kwargs) -> None:
        """Delete a message template (legacy alias).

        Args:
            name: Name of the template to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            await prompt_client.delete_prompt("old_template")
            ```
        """
        await self.delete_message_template(name=name, **kwargs)

    async def list_prompts(self, **kwargs) -> List[MessageTemplateAdapter]:
        """Get all message templates (legacy alias).

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MessageTemplateAdapter instances

        Example:
            ```python
            prompts = await prompt_client.list_prompts()
            ```
        """
        return await self.get_message_templates(**kwargs)

    # Template Management Utilities
    async def get_template_count(self, **kwargs) -> int:
        """Get the total number of message templates.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Total count of templates as integer

        Example:
            ```python
            count = await prompt_client.get_template_count()
            print(f"Total templates: {count}")
            ```
        """
        templates = await self.get_message_templates(**kwargs)
        return len(templates)

    async def search_templates_by_name(
        self, name_pattern: str, **kwargs
    ) -> List[MessageTemplateAdapter]:
        """Search templates by name pattern (case-insensitive).

        Args:
            name_pattern: Pattern to search for in template names
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MessageTemplateAdapter instances matching the pattern

        Example:
            ```python
            # Find all templates with "greeting" in the name
            templates = await prompt_client.search_templates_by_name("greeting")
            for t in templates:
                print(f"Found: {t.name}")
            ```
        """
        all_templates = await self.get_message_templates(**kwargs)
        return [
            template
            for template in all_templates
            if template.name and name_pattern.lower() in template.name.lower()
        ]

    async def get_templates_with_model(
        self, model_name: str, **kwargs
    ) -> List[MessageTemplateAdapter]:
        """Get templates that use a specific AI model.

        Args:
            model_name: Name of the AI model (e.g., "gpt-4", "gpt-3.5-turbo")
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MessageTemplateAdapter instances compatible with the model

        Example:
            ```python
            # Get all templates compatible with GPT-4
            gpt4_templates = await prompt_client.get_templates_with_model("gpt-4")
            ```
        """
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
        """Test a prompt with variables and AI model configuration.

        Convenience method that constructs a test request and executes it.

        Args:
            prompt_text: The prompt template text with variables
            variables: Dictionary of variable values to substitute
            ai_integration: Name of the AI integration provider
            text_complete_model: Name of the AI model to use
            temperature: Sampling temperature (0.0 to 1.0). Lower is more deterministic. Defaults to 0.1
            top_p: Nucleus sampling parameter. Defaults to 0.9
            stop_words: Optional list of stop words/sequences
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            String containing the AI model's response

        Example:
            ```python
            # Test a prompt with GPT-4
            result = await prompt_client.test_prompt(
                prompt_text="Summarize this for ${audience}: ${text}",
                variables={
                    "audience": "executives",
                    "text": "Long technical document..."
                },
                ai_integration="my-openai",
                text_complete_model="gpt-4",
                temperature=0.3,
                top_p=0.95
            )
            print(f"AI Response: {result}")
            ```
        """
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
