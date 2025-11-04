import os
import uuid

import pytest
import pytest_asyncio

from conductor.asyncio_client.adapters.api_client_adapter import \
    ApiClientAdapter as ApiClient
from conductor.asyncio_client.adapters.models.tag_adapter import \
    TagAdapter as MetadataTag
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.rest import ApiException
from conductor.asyncio_client.orkes.orkes_prompt_client import \
    OrkesPromptClient


class TestOrkesPromptClientIntegration:
    """
    Integration tests for OrkesPromptClient.

    Environment Variables:
    - CONDUCTOR_SERVER_URL: Base URL for Conductor server (default: http://localhost:8080/api)
    - CONDUCTOR_AUTH_KEY: Authentication key for Orkes
    - CONDUCTOR_AUTH_SECRET: Authentication secret for Orkes
    - CONDUCTOR_UI_SERVER_URL: UI server URL (optional)
    - CONDUCTOR_TEST_TIMEOUT: Test timeout in seconds (default: 30)
    - CONDUCTOR_TEST_CLEANUP: Whether to cleanup test resources (default: true)
    """

    @pytest.fixture(scope="class")
    def configuration(self) -> Configuration:
        config = Configuration()
        config.debug = os.getenv("CONDUCTOR_DEBUG", "false").lower() == "true"
        config.apply_logging_config()
        return config

    @pytest_asyncio.fixture(scope="function")
    async def prompt_client(self, configuration: Configuration) -> OrkesPromptClient:
        async with ApiClient(configuration) as api_client:
            return OrkesPromptClient(configuration, api_client)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_prompt_name(self, test_suffix: str) -> str:
        return f"test_prompt_{test_suffix}"

    @pytest.fixture(scope="class")
    def simple_prompt_template(self) -> str:
        return "Hello ${name}, welcome to ${company}!"

    @pytest.fixture(scope="class")
    def complex_prompt_template(self) -> str:
        return """
                You are a helpful assistant for ${company}.

                Customer Information:
                - Name: ${customer_name}
                - Email: ${customer_email}
                - Issue: ${issue_description}

                Please provide a ${response_type} response to the customer's inquiry.

                Guidelines:
                - Be ${tone} in your response
                - Include relevant ${company} policies
                - Keep the response under ${max_length} words

                Response:
                """

    @pytest.fixture(scope="class")
    def simple_variables(self) -> dict:
        return {"name": "John", "company": "Acme Corp"}

    @pytest.fixture(scope="class")
    def complex_variables(self) -> dict:
        return {
            "company": "TechCorp",
            "customer_name": "Alice Johnson",
            "customer_email": "alice@example.com",
            "issue_description": "Unable to access the dashboard",
            "response_type": "detailed",
            "tone": "professional",
            "max_length": "200",
        }

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_prompt_lifecycle_simple(
        self,
        prompt_client: OrkesPromptClient,
        test_prompt_name: str,
        simple_prompt_template: str,
    ):
        try:
            description = "A simple greeting prompt template"
            await prompt_client.save_prompt(
                test_prompt_name, description, simple_prompt_template
            )

            retrieved_prompt = await prompt_client.get_message_template(
                test_prompt_name
            )
            assert retrieved_prompt.name == test_prompt_name
            assert retrieved_prompt.description == description
            assert retrieved_prompt.template == simple_prompt_template
            assert "name" in retrieved_prompt.variables
            assert "company" in retrieved_prompt.variables

            prompts = await prompt_client.get_message_templates()
            prompt_names = [p.name for p in prompts]
            assert test_prompt_name in prompt_names

        except Exception as e:
            print(f"Exception in test_prompt_lifecycle_simple: {str(e)}")
            raise
        finally:
            try:
                await prompt_client.delete_prompt(test_prompt_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup prompt {test_prompt_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_prompt_lifecycle_complex(
        self,
        prompt_client: OrkesPromptClient,
        test_suffix: str,
        complex_prompt_template: str,
    ):
        prompt_name = f"test_complex_prompt_{test_suffix}"
        try:
            description = "A complex customer service prompt template"
            await prompt_client.save_prompt(
                prompt_name, description, complex_prompt_template
            )

            retrieved_prompt = await prompt_client.get_prompt(prompt_name)
            assert retrieved_prompt.name == prompt_name
            assert retrieved_prompt.description == description
            assert "company" in retrieved_prompt.variables
            assert "customer_name" in retrieved_prompt.variables
            assert "issue_description" in retrieved_prompt.variables

        except Exception as e:
            print(f"Exception in test_prompt_lifecycle_complex: {str(e)}")
            raise
        finally:
            try:
                await prompt_client.delete_prompt(prompt_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup prompt {prompt_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_prompt_with_tags(
        self,
        prompt_client: OrkesPromptClient,
        test_suffix: str,
        simple_prompt_template: str,
    ):
        prompt_name = f"test_tagged_prompt_{test_suffix}"
        try:
            description = "A prompt template with tags"
            await prompt_client.save_prompt(
                prompt_name, description, simple_prompt_template
            )

            tags = [
                MetadataTag(key="category", value="greeting", type="METADATA"),
                MetadataTag(key="language", value="english", type="METADATA"),
                MetadataTag(key="priority", value="high", type="METADATA"),
            ]
            await prompt_client.put_tag_for_prompt_template(prompt_name, tags)

            retrieved_tags = await prompt_client.get_tags_for_prompt_template(
                prompt_name
            )
            assert len(retrieved_tags) == 3
            tag_keys = [tag.key for tag in retrieved_tags]
            assert "category" in tag_keys
            assert "language" in tag_keys
            assert "priority" in tag_keys

            tags_to_delete = [
                MetadataTag(key="priority", value="high", type="METADATA")
            ]
            await prompt_client.delete_tag_for_prompt_template(
                prompt_name, tags_to_delete
            )

            retrieved_tags_after_delete = (
                await prompt_client.get_tags_for_prompt_template(prompt_name)
            )
            remaining_tag_keys = [tag.key for tag in retrieved_tags_after_delete]
            assert "priority" not in remaining_tag_keys
            assert len(retrieved_tags_after_delete) == 2

        except Exception as e:
            print(f"Exception in test_prompt_with_tags: {str(e)}")
            raise
        finally:
            try:
                await prompt_client.delete_prompt(prompt_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup prompt {prompt_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_prompt_update(
        self,
        prompt_client: OrkesPromptClient,
        test_suffix: str,
        simple_prompt_template: str,
    ):
        prompt_name = f"test_prompt_update_{test_suffix}"
        try:
            initial_description = "Initial description"
            initial_template = simple_prompt_template
            await prompt_client.save_prompt(
                prompt_name, initial_description, initial_template
            )

            retrieved_prompt = await prompt_client.get_prompt(prompt_name)
            assert retrieved_prompt.description == initial_description
            assert retrieved_prompt.template == initial_template

            updated_description = "Updated description"
            updated_template = (
                "Hello ${name}, welcome to ${company}! We're glad to have you here."
            )
            await prompt_client.save_prompt(
                prompt_name, updated_description, updated_template
            )

            updated_prompt = await prompt_client.get_prompt(prompt_name)
            assert updated_prompt.description == updated_description
            assert updated_prompt.template == updated_template
            assert "name" in updated_prompt.variables
            assert "company" in updated_prompt.variables

        except Exception as e:
            print(f"Exception in test_prompt_update: {str(e)}")
            raise
        finally:
            try:
                await prompt_client.delete_prompt(prompt_name)
            except Exception as e:
                print(f"Warning: Failed to cleanup prompt {prompt_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_prompt_tag_update_method(
        self, prompt_client: OrkesPromptClient, test_suffix: str
    ):
        """Test update_tag_for_prompt_template method."""
        prompt_name = f"test_tag_update_prompt_{test_suffix}"

        try:
            await prompt_client.save_prompt(
                prompt_name,
                "Test prompt for tag update",
                "Hello {{name}}"
            )

            tags = [
                MetadataTag(key="version", value="1.0", type="METADATA"),
                MetadataTag(key="environment", value="test", type="METADATA"),
            ]

            await prompt_client.update_tag_for_prompt_template(prompt_name, tags)

            retrieved_tags = await prompt_client.get_tags_for_prompt_template(prompt_name)
            assert len(retrieved_tags) == 2
            tag_keys = [tag.key for tag in retrieved_tags]
            assert "version" in tag_keys
            assert "environment" in tag_keys
        except Exception as e:
            print(f"Exception in test_prompt_tag_update_method: {str(e)}")
            raise
        finally:
            try:
                await prompt_client.delete_prompt(prompt_name)
            except Exception:
                pass
