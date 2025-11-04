from __future__ import absolute_import, annotations

from typing import List, Optional

from conductor.client.codegen.rest import ApiException
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.prompt_template_test_request import PromptTemplateTestRequest
from conductor.client.http.models.tag import Tag
from conductor.client.orkes.orkes_base_client import OrkesBaseClient
from conductor.client.prompt_client import PromptClient
from conductor.client.http.models.message_template import MessageTemplate


class OrkesPromptClient(OrkesBaseClient, PromptClient):
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def save_prompt(
        self, prompt_name: str, description: str, prompt_template: str, **kwargs
    ) -> None:
        self._prompt_api.save_message_template(
            body=prompt_template, description=description, name=prompt_name, **kwargs
        )

    def get_prompt(self, prompt_name: str, **kwargs) -> Optional[MessageTemplate]:
        try:
            return self._prompt_api.get_message_template(name=prompt_name, **kwargs)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_prompts(self, **kwargs) -> List[MessageTemplate]:
        return self._prompt_api.get_message_templates(**kwargs)

    def delete_prompt(self, prompt_name: str, **kwargs) -> None:
        self._prompt_api.delete_message_template(name=prompt_name, **kwargs)

    def get_tags_for_prompt_template(self, prompt_name: str, **kwargs) -> List[Tag]:
        return self._prompt_api.get_tags_for_prompt_template(name=prompt_name, **kwargs)

    def update_tag_for_prompt_template(self, prompt_name: str, tags: List[Tag], **kwargs) -> None:
        self._prompt_api.put_tag_for_prompt_template(body=tags, name=prompt_name, **kwargs)

    def delete_tag_for_prompt_template(self, prompt_name: str, tags: List[Tag], **kwargs) -> None:
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
        self._prompt_api.create_message_templates(body=body, **kwargs)
