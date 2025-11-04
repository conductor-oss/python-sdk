import os
import pytest
import uuid
import threading
import time

from conductor.client.configuration.configuration import Configuration
from conductor.client.orkes.orkes_integration_client import OrkesIntegrationClient
from conductor.client.http.models.integration_update import (
    IntegrationUpdateAdapter as IntegrationUpdate,
)
from conductor.client.http.models.integration_api_update import (
    IntegrationApiUpdateAdapter as IntegrationApiUpdate,
)
from conductor.client.orkes.models.metadata_tag import MetadataTag
from conductor.client.codegen.rest import ApiException


class TestOrkesIntegrationClientIntegration:
    """
    Integration tests for OrkesIntegrationClient covering all endpoints.

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

    @pytest.fixture(scope="class")
    def integration_client(self, configuration: Configuration) -> OrkesIntegrationClient:
        return OrkesIntegrationClient(configuration)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def simple_integration_config(self) -> dict:
        return {
            "awsAccountId": "test_account_id",
        }

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_save_and_get_integration_provider(
        self,
        integration_client: OrkesIntegrationClient,
        test_suffix: str,
        simple_integration_config: dict,
    ):
        integration_name = f"openai_{test_suffix}"
        integration_update = IntegrationUpdate(
            category="AI_MODEL",
            type="openai",
            description="Test integration provider",
            enabled=True,
            configuration=simple_integration_config,
        )

        try:
            integration_client.save_integration_provider(integration_name, integration_update)
            retrieved_integration = integration_client.get_integration_provider(integration_name)

            assert retrieved_integration.name == integration_name
            assert retrieved_integration.category == integration_update.category
            assert retrieved_integration.type == integration_update.type
            assert retrieved_integration.description == integration_update.description
            assert retrieved_integration.enabled == integration_update.enabled
        finally:
            self._cleanup_integration(integration_client, integration_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_save_and_get_integration(
        self,
        integration_client: OrkesIntegrationClient,
        test_suffix: str,
        simple_integration_config: dict,
    ):
        integration_name = f"test_integration_{test_suffix}"
        integration_update = IntegrationUpdate(
            category="AI_MODEL",
            type="openai",
            description="Test integration",
            enabled=True,
            configuration=simple_integration_config,
        )

        try:
            integration_client.save_integration(integration_name, integration_update)
            retrieved_integration = integration_client.get_integration(integration_name)

            assert retrieved_integration.name == integration_name
            assert retrieved_integration.category == integration_update.category
            assert retrieved_integration.type == integration_update.type
            assert retrieved_integration.description == integration_update.description
            assert retrieved_integration.enabled == integration_update.enabled
        finally:
            self._cleanup_integration(integration_client, integration_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_get_integration_providers(
        self,
        integration_client: OrkesIntegrationClient,
        test_suffix: str,
        simple_integration_config: dict,
    ):
        integration_name = f"test_providers_{test_suffix}"
        integration_update = IntegrationUpdate(
            category="AI_MODEL",
            type="openai",
            description="Test integration providers",
            enabled=True,
            configuration=simple_integration_config,
        )

        try:
            integration_client.save_integration_provider(integration_name, integration_update)

            all_providers = integration_client.get_integration_providers()
            assert isinstance(all_providers, list)

            provider_names = [provider.name for provider in all_providers]
            assert integration_name in provider_names

            ai_providers = integration_client.get_integration_providers(category="AI_MODEL")
            assert isinstance(ai_providers, list)

            active_providers = integration_client.get_integration_providers(active_only=True)
            assert isinstance(active_providers, list)
        finally:
            self._cleanup_integration(integration_client, integration_name)

    @pytest.mark.v4_1_73
    def test_get_integration_provider_defs(
        self,
        integration_client: OrkesIntegrationClient,
    ):
        provider_defs = integration_client.get_integration_provider_defs()
        assert isinstance(provider_defs, list)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_get_all_integrations(
        self,
        integration_client: OrkesIntegrationClient,
        test_suffix: str,
        simple_integration_config: dict,
    ):
        integration_name = f"test_all_integrations_{test_suffix}"

        integration_update = IntegrationUpdate(
            category="AI_MODEL",
            type="openai",
            description="Test integration for all integrations",
            enabled=True,
            configuration=simple_integration_config,
        )

        try:
            integration_client.save_integration_provider(integration_name, integration_update)

            all_integrations = integration_client.get_all_integrations()
            assert isinstance(all_integrations, list)

            integration_names = [integration.name for integration in all_integrations]
            assert integration_name in integration_names

            ai_integrations = integration_client.get_all_integrations(category="AI_MODEL")
            assert isinstance(ai_integrations, list)

            active_integrations = integration_client.get_all_integrations(active_only=True)
            assert isinstance(active_integrations, list)
        finally:
            self._cleanup_integration(integration_client, integration_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_get_providers_and_integrations(
        self,
        integration_client: OrkesIntegrationClient,
        test_suffix: str,
        simple_integration_config: dict,
    ):
        integration_name = f"test_providers_and_integrations_{test_suffix}"

        integration_update = IntegrationUpdate(
            category="AI_MODEL",
            type="openai",
            description="Test integration for providers and integrations",
            enabled=True,
            configuration=simple_integration_config,
        )

        try:
            integration_client.save_integration_provider(integration_name, integration_update)

            providers_and_integrations = integration_client.get_providers_and_integrations()
            assert isinstance(providers_and_integrations, list)

            openai_providers = integration_client.get_providers_and_integrations(integration_type="openai")
            assert isinstance(openai_providers, list)

            active_providers = integration_client.get_providers_and_integrations(active_only=True)
            assert isinstance(active_providers, list)
        finally:
            self._cleanup_integration(integration_client, integration_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_integration_provider_tags(
        self,
        integration_client: OrkesIntegrationClient,
        test_suffix: str,
        simple_integration_config: dict,
    ):
        integration_name = f"test_provider_tags_{test_suffix}"

        integration_update = IntegrationUpdate(
            category="AI_MODEL",
            type="openai",
            description="Test integration for provider tags",
            enabled=True,
            configuration=simple_integration_config,
        )

        try:
            integration_client.save_integration_provider(integration_name, integration_update)

            tag = MetadataTag("priority", "high"),

            integration_client.put_tag_for_integration_provider(tag, integration_name)

            retrieved_tags = integration_client.get_tags_for_integration_provider(integration_name)
            assert len(retrieved_tags) == 1
            tag_keys = [tag.key for tag in retrieved_tags]
            assert "priority" in tag_keys

            tag_to_delete = MetadataTag("priority", "high")
            integration_client.delete_tag_for_integration_provider(tag_to_delete, integration_name)

            retrieved_tags_after_delete = integration_client.get_tags_for_integration_provider(integration_name)
            remaining_tag_keys = [tag.key for tag in retrieved_tags_after_delete]
            assert "priority" not in remaining_tag_keys
        finally:
            self._cleanup_integration(integration_client, integration_name)

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_integration_not_found(self, integration_client: OrkesIntegrationClient):
        non_existent_integration = f"non_existent_{str(uuid.uuid4())}"
        non_existent_api = f"non_existent_api_{str(uuid.uuid4())}"

        retrieved_integration = integration_client.get_integration(non_existent_integration)
        assert retrieved_integration is None

        retrieved_api = integration_client.get_integration_api(non_existent_api, non_existent_integration)
        assert retrieved_api is None

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_concurrent_integration_operations(
        self,
        integration_client: OrkesIntegrationClient,
        test_suffix: str,
        simple_integration_config: dict,
    ):
        results = []
        errors = []
        created_integrations = []
        cleanup_lock = threading.Lock()

        def create_and_manage_integration(integration_suffix: str):
            integration_name = None
            try:
                integration_name = f"concurrent_integration_{integration_suffix}"
                integration_update = IntegrationUpdate(
                    category="AI_MODEL",
                    type="openai",
                    description="Concurrent test integration",
                    enabled=True,
                    configuration=simple_integration_config,
                )

                integration_client.save_integration_provider(integration_name, integration_update)

                with cleanup_lock:
                    created_integrations.append(integration_name)

                time.sleep(0.1)

                retrieved_integration = integration_client.get_integration_provider(integration_name)
                assert retrieved_integration.name == integration_name

                if os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true":
                    try:
                        integration_client.delete_integration(integration_name)
                        with cleanup_lock:
                            if integration_name in created_integrations:
                                created_integrations.remove(integration_name)
                    except Exception as cleanup_error:
                        print(f"Warning: Failed to cleanup integration {integration_name} in thread: {str(cleanup_error)}")

                results.append(f"integration_{integration_suffix}_success")
            except Exception as e:
                errors.append(f"integration_{integration_suffix}_error: {str(e)}")
                if integration_name and integration_name not in created_integrations:
                    with cleanup_lock:
                        created_integrations.append(integration_name)

        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=create_and_manage_integration, args=(f"{test_suffix}_{i}",)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        assert len(results) == 3, f"Expected 3 successful operations, got {len(results)}. Errors: {errors}"
        assert len(errors) == 0, f"Unexpected errors: {errors}"

        for integration_name in created_integrations:
            try:
                integration_client.delete_integration(integration_name)
            except Exception as e:
                print(f"Warning: Failed to delete integration {integration_name}: {str(e)}")

    def _cleanup_integration(self, integration_client: OrkesIntegrationClient, integration_name: str):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        try:
            integration_client.delete_integration(integration_name)
        except Exception as e:
            print(f"Warning: Failed to cleanup integration {integration_name}: {str(e)}")

    def _cleanup_integration_api(self, integration_client: OrkesIntegrationClient, api_name: str, integration_name: str):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        try:
            integration_client.delete_integration_api(api_name, integration_name)
        except Exception as e:
            print(f"Warning: Failed to cleanup integration API {api_name}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    def test_save_and_get_integration(
        self, integration_client: OrkesIntegrationClient, test_suffix: str, simple_integration_config: dict
    ):
        """Test save_integration and get_integration methods."""
        integration_name = f"test_save_integration_{test_suffix}"

        try:
            integration_update = IntegrationUpdate(
                category="AI_MODEL",
                type="openai",
                description="Test save_integration method",
                enabled=True,
                configuration=simple_integration_config,
            )

            integration_client.save_integration(integration_name, integration_update)

            retrieved_integration = integration_client.get_integration(integration_name)
            assert retrieved_integration is not None
            assert retrieved_integration.enabled is True

            non_existent = integration_client.get_integration(f"non_existent_{test_suffix}")
            assert non_existent is None
        except Exception as e:
            print(f"Exception in test_save_and_get_integration: {str(e)}")
            raise
        finally:
            self._cleanup_integration(integration_client, integration_name)
