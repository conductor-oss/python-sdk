from __future__ import absolute_import, annotations

from typing import List, Optional

from conductor.client.codegen.rest import ApiException
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.message_template import MessageTemplate
from conductor.client.http.models.prompt_template_test_request import PromptTemplateTestRequest
from conductor.client.http.models.tag import Tag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.prompt_client import PromptClient


class OrkesPromptClient(OrkesBaseClient, PromptClient):
    def __init__(self, configuration: Configuration):
        """Initialize the OrkesPromptClient with configuration.

        Args:
            configuration: Configuration object containing server settings and authentication

        Example:
            ```python
            from conductor.client.configuration.configuration import Configuration

            config = Configuration(server_api_url="http://localhost:8080/api")
            prompt_client = OrkesPromptClient(config)
            ```
        """
        super().__init__(configuration)

    def save_prompt(
        self, prompt_name: str, description: str, prompt_template: str, **kwargs
    ) -> None:
        """Create or update a prompt template.

        Args:
            prompt_name: Unique name for the template
            description: Human-readable description of the template's purpose
            prompt_template: Template text with variables in ${variable} format
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            # Create a customer service template
            prompt_client.save_prompt(
                "customer_greeting",
                "Greeting template for customer service",
                "Hello ${customer_name}, welcome to ${company}! How can I help you today?"
            )
            ```
        """
        self._prompt_api.save_message_template(
            body=prompt_template, description=description, name=prompt_name, **kwargs
        )

    def get_prompt(self, prompt_name: str, **kwargs) -> Optional[MessageTemplate]:
        """Get a prompt template by name.

        Args:
            prompt_name: Name of the template to retrieve
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            MessageTemplate instance if found, None otherwise

        Example:
            ```python
            template = prompt_client.get_prompt("customer_greeting")
            if template:
                print(f"Template: {template.template}")
            ```
        """
        try:
            return self._prompt_api.get_message_template(name=prompt_name, **kwargs)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_prompts(self, **kwargs) -> List[MessageTemplate]:
        """Get all prompt templates.

        Args:
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of MessageTemplate instances

        Example:
            ```python
            templates = prompt_client.get_prompts()
            for template in templates:
                print(f"Template: {template.name}, Description: {template.description}")
            ```
        """
        return self._prompt_api.get_message_templates(**kwargs)

    def delete_prompt(self, prompt_name: str, **kwargs) -> None:
        """Delete a prompt template by name.

        Args:
            prompt_name: Name of the template to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            prompt_client.delete_prompt("old_template")
            ```
        """
        self._prompt_api.delete_message_template(name=prompt_name, **kwargs)

    def get_tags_for_prompt_template(self, prompt_name: str, **kwargs) -> List[Tag]:
        """Get tags for a prompt template.

        Args:
            prompt_name: Name of the template
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            List of Tag instances

        Example:
            ```python
            tags = prompt_client.get_tags_for_prompt_template("customer_greeting")
            for tag in tags:
                print(f"Tag: {tag.key}={tag.value}")
            ```
        """
        return self._prompt_api.get_tags_for_prompt_template(name=prompt_name, **kwargs)

    def update_tag_for_prompt_template(self, prompt_name: str, tags: List[Tag], **kwargs) -> None:
        """Update tags for a prompt template.

        Args:
            prompt_name: Name of the template
            tags: List of tags to set
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags = [
                Tag(key="category", value="customer_service"),
                Tag(key="language", value="english")
            ]
            prompt_client.update_tag_for_prompt_template("customer_greeting", tags)
            ```
        """
        self._prompt_api.put_tag_for_prompt_template(body=tags, name=prompt_name, **kwargs)

    def delete_tag_for_prompt_template(self, prompt_name: str, tags: List[Tag], **kwargs) -> None:
        """Delete tags for a prompt template.

        Args:
            prompt_name: Name of the template
            tags: List of tags to delete
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.tag import Tag

            tags_to_delete = [Tag(key="category", value="old_category")]
            prompt_client.delete_tag_for_prompt_template("customer_greeting", tags_to_delete)
            ```
        """
        self._prompt_api.delete_tag_for_prompt_template(body=tags, name=prompt_name, **kwargs)

    def test_prompt(
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
        """Test a prompt template with AI model.

        Args:
            prompt_text: Prompt template text to test
            variables: Dictionary of variable values for substitution
            ai_integration: Name of the AI integration (e.g., "openai")
            text_complete_model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
            temperature: Sampling temperature (0.0 to 1.0), default 0.1
            top_p: Nucleus sampling parameter (0.0 to 1.0), default 0.9
            stop_words: Optional list of stop words
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            Generated text from the AI model

        Example:
            ```python
            result = prompt_client.test_prompt(
                prompt_text="Summarize this: ${text}",
                variables={"text": "Long article content..."},
                ai_integration="openai",
                text_complete_model="gpt-4",
                temperature=0.7,
                top_p=0.9
            )
            print(f"Generated: {result}")
            ```
        """
        request = PromptTemplateTestRequest()
        request.prompt = prompt_text
        request.llm_provider = ai_integration
        request.model = text_complete_model
        request.prompt_variables = variables
        request.temperature = temperature
        request.top_p = top_p
        if stop_words is not None:
            request.stop_words = stop_words
        return self._prompt_api.test_message_template(request, **kwargs)

    def create_message_templates(self, body: List[MessageTemplate], **kwargs) -> None:
        """Create multiple message templates in bulk.

        Args:
            body: List of message templates to create
            **kwargs: Additional optional parameters to pass to the API

        Returns:
            None

        Example:
            ```python
            from conductor.client.http.models.message_template import MessageTemplate

            templates = [
                MessageTemplate(
                    name="greeting",
                    description="Greeting template",
                    template="Hello ${name}!"
                ),
                MessageTemplate(
                    name="farewell",
                    description="Farewell template",
                    template="Goodbye ${name}, see you soon!"
                )
            ]
            prompt_client.create_message_templates(templates)
            ```
        """
        self._prompt_api.create_message_templates(body=body, **kwargs)
