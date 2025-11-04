from typing import List

from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.api.prompt_resource_api import PromptResourceApi
from conductor.client.http.models.message_template import MessageTemplate
from conductor.client.http.models.prompt_template_test_request import PromptTemplateTestRequest
from conductor.client.http.models.tag import Tag


class PromptResourceApiAdapter:
    def __init__(self, api_client: ApiClientAdapter):
        self._api = PromptResourceApi(api_client)

    def create_message_templates(self, body: List[MessageTemplate], **kwargs) -> None:
        """Create message templates in bulk"""
        return self._api.create_message_templates(body, **kwargs)

    def delete_message_template(self, name: str, **kwargs) -> None:
        """Delete a message template"""
        return self._api.delete_message_template(name, **kwargs)

    def delete_tag_for_prompt_template(self, body: List[Tag], name: str, **kwargs) -> None:
        """Delete a tag for a prompt template"""
        return self._api.delete_tag_for_prompt_template(body, name, **kwargs)

    def get_message_template(self, name: str, **kwargs) -> MessageTemplate:
        """Get a message template"""
        return self._api.get_message_template(name, **kwargs)

    def get_message_templates(self, **kwargs) -> List[MessageTemplate]:
        """Get all message templates"""
        return self._api.get_message_templates(**kwargs)

    def get_tags_for_prompt_template(self, name: str, **kwargs) -> List[Tag]:
        """Get tags for a prompt template"""
        return self._api.get_tags_for_prompt_template(name, **kwargs)

    def put_tag_for_prompt_template(self, body: List[Tag], name: str, **kwargs) -> None:
        """Put a tag for a prompt template"""
        return self._api.put_tag_for_prompt_template(body, name, **kwargs)

    def save_message_template(self, body: str, description: str, name: str, **kwargs) -> None:
        """Save a message template"""
        return self._api.save_message_template(body, description, name, **kwargs)

    def test_message_template(self, body: PromptTemplateTestRequest, **kwargs) -> str:
        """Test a message template"""
        return self._api.test_message_template(body, **kwargs)
