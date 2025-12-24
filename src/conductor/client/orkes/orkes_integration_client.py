from __future__ import absolute_import

from typing import List

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.models.integration import Integration
from conductor.client.http.models.integration_api import IntegrationApi
from conductor.client.http.models.integration_api_update import IntegrationApiUpdate
from conductor.client.http.models.integration_update import IntegrationUpdate
from conductor.client.http.models.prompt_template import PromptTemplate
from conductor.client.http.rest import ApiException
from conductor.client.integration_client import IntegrationClient
from conductor.client.orkes.orkes_base_client import OrkesBaseClient


class OrkesIntegrationClient(OrkesBaseClient, IntegrationClient):

    def __init__(self, configuration: Configuration):
        super(OrkesIntegrationClient, self).__init__(configuration)

    def associate_prompt_with_integration(self, ai_integration: str, model_name: str, prompt_name: str):
        self.integrationApi.associate_prompt_with_integration(ai_integration, model_name, prompt_name)

    def delete_integration_api(self, api_name: str, integration_name: str):
        self.integrationApi.delete_integration_api(api_name, integration_name)

    def delete_integration(self, integration_name: str):
        self.integrationApi.delete_integration_provider(integration_name)

    def get_integration_api(self, api_name: str, integration_name: str) -> IntegrationApi:
        try:
            return self.integrationApi.get_integration_api(api_name, integration_name)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integration_apis(self, integration_name: str) -> List[IntegrationApi]:
        return self.integrationApi.get_integration_apis(integration_name)

    def get_integration(self, integration_name: str) -> Integration:
        try:
            return self.integrationApi.get_integration_provider(integration_name)
        except ApiException as e:
            if e.is_not_found():
                return None
            raise e

    def get_integrations(self) -> List[Integration]:
        return self.integrationApi.get_integration_providers()

    def get_prompts_with_integration(self, ai_integration: str, model_name: str) -> List[PromptTemplate]:
        return self.integrationApi.get_prompts_with_integration(ai_integration, model_name)

    def save_integration_api(self, integration_name, api_name, api_details: IntegrationApiUpdate):
        self.integrationApi.save_integration_api(api_details, integration_name, api_name)

    def save_integration(self, integration_name, integration_details: IntegrationUpdate):
        self.integrationApi.save_integration_provider(integration_details, integration_name)

    def get_token_usage_for_integration(self, name, integration_name) -> int:
        return self.integrationApi.get_token_usage_for_integration(name, integration_name)

    def get_token_usage_for_integration_provider(self, name) -> dict:
        return self.integrationApi.get_token_usage_for_integration_provider(name)

    # Tags

    def delete_tag_for_integration(self, body, tag_name, integration_name):
        """Delete tags for an integration API"""
        self.integrationApi.delete_tag_for_integration(body, tag_name, integration_name)

    def delete_tag_for_integration_provider(self, body, name):
        self.integrationApi.delete_tag_for_integration_provider(body, name)

    def put_tag_for_integration(self, body, name, integration_name):
        self.integrationApi.put_tag_for_integration(body, name, integration_name)

    def put_tag_for_integration_provider(self, body, name):
        self.integrationApi.put_tag_for_integration_provider(body, name)

    def get_tags_for_integration(self, name, integration_name):
        return self.integrationApi.get_tags_for_integration(name, integration_name)

    def get_tags_for_integration_provider(self, name):
        return self.integrationApi.get_tags_for_integration_provider(name)

    # Additional methods

    def get_integration_available_apis(self, integration_name):
        """Get available APIs for an integration provider"""
        return self.integrationApi.get_integration_available_apis(integration_name)

    def get_integration_provider_defs(self):
        """Get all integration provider definitions"""
        return self.integrationApi.get_integration_provider_defs()

    def get_providers_and_integrations(self):
        """Get all providers and their integrations"""
        return self.integrationApi.get_providers_and_integrations()
