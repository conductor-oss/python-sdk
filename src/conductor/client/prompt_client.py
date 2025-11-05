from __future__ import absolute_import, annotations

from abc import ABC, abstractmethod
from typing import List, Optional

# python 2 and python 3 compatibility library
from conductor.client.http.models.message_template import MessageTemplate
from conductor.client.http.models.tag import Tag


class PromptClient(ABC):
    @abstractmethod
    def save_prompt(self, prompt_name: str, description: str, prompt_template: str):
        pass

    @abstractmethod
    def get_prompt(self, prompt_name: str, **kwargs) -> Optional[MessageTemplate]:
        pass

    @abstractmethod
    def get_prompts(self):
        pass

    @abstractmethod
    def delete_prompt(self, prompt_name: str):
        pass

    @abstractmethod
    def get_tags_for_prompt_template(self, prompt_name: str, **kwargs) -> List[Tag]:
        pass

    @abstractmethod
    def update_tag_for_prompt_template(self, prompt_name: str, tags: List[Tag], **kwargs) -> None:
        pass

    @abstractmethod
    def delete_tag_for_prompt_template(self, prompt_name: str, tags: List[Tag]):
        pass

    @abstractmethod
    def test_prompt(
        self,
        prompt_text: str,
        variables: dict,
        ai_integration: str,
        text_complete_model: str,
        temperature: float = 0.1,
        top_p: float = 0.9,
        stop_words: Optional[List[str]] = None,
    ) -> str:
        pass
