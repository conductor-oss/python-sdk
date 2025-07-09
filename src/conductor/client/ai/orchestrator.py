from __future__ import annotations

from typing import Optional, List
from uuid import uuid4

from typing_extensions import Self

from conductor.client.ai.configuration import LLMProvider, VectorDB
from conductor.client.ai.integrations import IntegrationConfig
from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.http.models.prompt_template import PromptTemplate
from conductor.client.http.rest import ApiException
from conductor.client.orkes_clients import OrkesClients


class AIOrchestrator:
    def __init__(self, api_configuration: Configuration, prompt_test_workflow_name: str = '') -> Self:
        orkes_clients = OrkesClients(api_configuration)

        self.integration_client = orkes_clients.get_integration_client()
        self.workflow_client = orkes_clients.get_workflow_client()
        self.workflow_executor = orkes_clients.get_workflow_executor()
        self.prompt_client = orkes_clients.get_prompt_client()

        self.prompt_test_workflow_name = prompt_test_workflow_name
        if self.prompt_test_workflow_name == '':
            self.prompt_test_workflow_name = 'prompt_test_' + str(uuid4())

    def add_prompt_template(self, name: str, prompt_template: str, description: str):
        self.prompt_client.save_prompt(name, description, prompt_template)
        return self

    def get_prompt_template(self, template_name: str) -> PromptTemplate:
        try:
            return self.prompt_client.get_prompt(template_name)
        except ApiException as e:
            if e.code == 404:
                return None
            raise e

    def associate_prompt_template(self, name: str, ai_integration: str, ai_models: List[str]):
        for ai_model in ai_models:
            self.integration_client.associate_prompt_with_integration(ai_integration, ai_model, name)

    def test_prompt_template(self, text: str, variables: dict,
                             ai_integration: str,
                             text_complete_model: str,
                             stop_words: Optional[List[str]] = [], max_tokens: Optional[int] = 100,
                             temperature: int = 0,
                             top_p: int = 1):

        return self.prompt_client.test_prompt(text, variables, ai_integration, text_complete_model, temperature, top_p,
                                              stop_words)

    def add_ai_integration(self, ai_integration_name: str, provider: LLMProvider, models: List[str], description: str,
                           config: IntegrationConfig, overwrite : bool = False):
        details = IntegrationUpdate()
        details.configuration = config.to_dict()
        details.type = provider.value
        details.category = 'AI_MODEL'
        details.enabled = True
        details.description = description
        existing_integration = self.integration_client.get_integration(integration_name=ai_integration_name)
        if existing_integration is None or overwrite:
            self.integration_client.save_integration(ai_integration_name, details)
        for model in models:
            api_details = IntegrationApiUpdate()
            api_details.enabled = True
            api_details.description = description
            existing_integration_api = self.integration_client.get_integration_api(ai_integration_name, model)
            if existing_integration_api is None or overwrite:
                self.integration_client.save_integration_api(ai_integration_name, model, api_details)

    def add_vector_store(self, db_integration_name: str, provider: VectorDB, indices: List[str],config: IntegrationConfig,
                         description: str = None,overwrite : bool = False):
        vector_db = IntegrationUpdate()
        vector_db.configuration = config.to_dict()
        vector_db.type = provider.value
        vector_db.category = 'VECTOR_DB'
        vector_db.enabled = True
        if description is None:
            description = db_integration_name
        vector_db.description = description
        existing_integration = self.integration_client.get_integration(db_integration_name)
        if existing_integration is None or overwrite:
            self.integration_client.save_integration(db_integration_name, vector_db)
        for index in indices:
            api_details = IntegrationApiUpdate()
            api_details.enabled = True
            api_details.description = description
            existing_integration_api = self.integration_client.get_integration_api(db_integration_name, index)
            if existing_integration_api is None or overwrite:
                self.integration_client.save_integration_api(db_integration_name, index, api_details)
        pass

    def get_token_used(self, ai_integration: str) -> dict:
        return self.integration_client.get_token_usage_for_integration_provider(ai_integration)

    def get_token_used_by_model(self, ai_integration: str, model: str) -> int:
        return self.integration_client.get_token_usage_for_integration(ai_integration, model)
