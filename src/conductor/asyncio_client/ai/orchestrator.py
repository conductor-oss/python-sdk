from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional
from uuid import uuid4

from conductor.asyncio_client.adapters.models.integration_api_update_adapter import \
    IntegrationApiUpdateAdapter
from conductor.asyncio_client.adapters.models.integration_update_adapter import \
    IntegrationUpdateAdapter
from conductor.asyncio_client.http.exceptions import NotFoundException
from conductor.asyncio_client.orkes.orkes_clients import OrkesClients

if TYPE_CHECKING:
    from conductor.asyncio_client.adapters.models.message_template_adapter import \
        MessageTemplateAdapter
    from conductor.asyncio_client.configuration import Configuration
    from conductor.shared.ai.configuration.interfaces.integration_config import \
        IntegrationConfig
    from conductor.shared.ai.enums import LLMProvider, VectorDB

NOT_FOUND_STATUS = 404


class AsyncAIOrchestrator:
    def __init__(
        self, api_configuration: Configuration, prompt_test_workflow_name: str = ""
    ):
        orkes_clients = OrkesClients(api_configuration)

        self.integration_client = orkes_clients.get_integration_client()
        self.workflow_client = orkes_clients.get_integration_client()
        self.workflow_executor = orkes_clients.get_workflow_executor()
        self.prompt_client = orkes_clients.get_prompt_client()

        self.prompt_test_workflow_name = prompt_test_workflow_name
        if self.prompt_test_workflow_name == "":
            self.prompt_test_workflow_name = "prompt_test_" + str(uuid4())

    async def add_prompt_template(
        self, name: str, prompt_template: str, description: str
    ):
        await self.prompt_client.save_prompt(name, description, prompt_template)
        return self

    async def get_prompt_template(
        self, template_name: str
    ) -> Optional[MessageTemplateAdapter]:
        try:
            return await self.prompt_client.get_prompt(template_name)
        except NotFoundException:
            return None

    async def associate_prompt_template(
        self, name: str, ai_integration: str, ai_models: List[str]
    ):
        for ai_model in ai_models:
            await self.integration_client.associate_prompt_with_integration(
                ai_integration, ai_model, name
            )

    async def test_prompt_template(
        self,
        text: str,
        variables: dict,
        ai_integration: str,
        text_complete_model: str,
        stop_words: Optional[List[str]] = None,
        max_tokens: int = 100,
        temperature: int = 0,
        top_p: int = 1,
    ):
        stop_words = stop_words or []
        return await self.prompt_client.test_prompt(
            text,
            variables,
            ai_integration,
            text_complete_model,
            temperature,
            top_p,
            stop_words,
        )

    async def add_ai_integration(
        self,
        ai_integration_name: str,
        provider: LLMProvider,
        models: List[str],
        description: str,
        config: IntegrationConfig,
        overwrite: bool = False,
    ):
        details = IntegrationUpdateAdapter(
            configuration=config.to_dict(),
            type=provider.value,
            category="AI_MODEL",
            enabled=True,
            description=description,
        )
        existing_integration = await self.integration_client.get_integration_provider(
            name=ai_integration_name
        )
        if existing_integration is None or overwrite:
            await self.integration_client.save_integration_provider(
                ai_integration_name, details
            )
        for model in models:
            api_details = IntegrationApiUpdateAdapter(
                enabled=True, description=description
            )
            existing_integration_api = (
                await self.integration_client.get_integration_api(
                    ai_integration_name, model
                )
            )
            if existing_integration_api is None or overwrite:
                await self.integration_client.save_integration_api(
                    ai_integration_name, model, api_details
                )

    async def add_vector_store(
        self,
        db_integration_name: str,
        provider: VectorDB,
        indices: List[str],
        config: IntegrationConfig,
        description: Optional[str] = None,
        overwrite: bool = False,
    ):
        vector_db = IntegrationUpdateAdapter(
            configuration=config.to_dict(),
            type=provider.value,
            category="VECTOR_DB",
            enabled=True,
            description=description or db_integration_name,
        )
        existing_integration = await self.integration_client.get_integration(
            db_integration_name
        )
        if existing_integration is None or overwrite:
            await self.integration_client.save_integration(
                db_integration_name, vector_db
            )
        for index in indices:
            api_details = IntegrationApiUpdateAdapter()
            api_details.enabled = True
            api_details.description = description
            existing_integration_api = (
                await self.integration_client.get_integration_api(
                    db_integration_name, index
                )
            )
            if existing_integration_api is None or overwrite:
                await self.integration_client.save_integration_api(
                    db_integration_name, index, api_details
                )

    async def get_token_used(self, ai_integration: str) -> int:
        return await self.integration_client.get_token_usage_for_integration_provider(
            ai_integration
        )

    async def get_token_used_by_model(self, ai_integration: str, model: str) -> int:
        return await self.integration_client.get_token_usage_for_integration(
            ai_integration, model
        )
