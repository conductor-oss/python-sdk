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
from conductor.asyncio_client.orkes.orkes_secret_client import \
    OrkesSecretClient


class TestOrkesSecretClientIntegration:
    """
    Integration tests for OrkesSecretClient.

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
    async def secret_client(self, configuration: Configuration) -> OrkesSecretClient:
        async with ApiClient(configuration) as api_client:
            return OrkesSecretClient(configuration, api_client)

    @pytest.fixture(scope="class")
    def test_suffix(self) -> str:
        return str(uuid.uuid4())[:8]

    @pytest.fixture(scope="class")
    def test_secret_key(self, test_suffix: str) -> str:
        return f"test_secret_{test_suffix}"

    @pytest.fixture(scope="class")
    def simple_secret_value(self) -> str:
        return "simple_secret_value_123"

    @pytest.fixture(scope="class")
    def complex_secret_value(self) -> str:
        return """{"api_key": "sk-1234567890abcdef", "database_url": "postgresql://user:pass@localhost:5432/db", "redis_password": "redis_secret_456", "jwt_secret": "jwt_secret_key_789", "encryption_key": "encryption_key_abc123"}"""

    @pytest.fixture(scope="class")
    def json_secret_value(self) -> str:
        return '{"username": "admin", "password": "secure_password_123", "role": "administrator"}'

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_secret_lifecycle_simple(
        self,
        secret_client: OrkesSecretClient,
        test_secret_key: str,
        simple_secret_value: str,
    ):
        try:
            await secret_client.put_secret(test_secret_key, simple_secret_value)

            retrieved_value = await secret_client.get_secret(test_secret_key)

            # Handle case where secret is returned as JSON string
            if retrieved_value.startswith('"') and retrieved_value.endswith('"'):
                import json

                retrieved_value = json.loads(retrieved_value)

            assert retrieved_value == simple_secret_value

            exists = await secret_client.secret_exists(test_secret_key)
            assert exists is True

            all_secrets = await secret_client.list_all_secret_names()
            assert test_secret_key in all_secrets

        except Exception as e:
            print(f"Exception in test_secret_lifecycle_simple: {str(e)}")
            raise
        finally:
            try:
                await secret_client.delete_secret(test_secret_key)
            except Exception as e:
                print(f"Warning: Failed to cleanup secret {test_secret_key}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_secret_lifecycle_complex(
        self,
        secret_client: OrkesSecretClient,
        test_suffix: str,
        complex_secret_value: str,
    ):
        secret_key = f"test_complex_secret_{test_suffix}"
        try:
            await secret_client.put_secret(secret_key, complex_secret_value)

            retrieved_value = await secret_client.get_secret(secret_key)
            assert retrieved_value is not None

            exists = await secret_client.secret_exists(secret_key)
            assert exists is True

        except Exception as e:
            print(f"Exception in test_secret_lifecycle_complex: {str(e)}")
            raise
        finally:
            try:
                await secret_client.delete_secret(secret_key)
            except Exception as e:
                print(f"Warning: Failed to cleanup secret {secret_key}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_secret_with_tags(
        self,
        secret_client: OrkesSecretClient,
        test_suffix: str,
        simple_secret_value: str,
    ):
        secret_key = f"test_tagged_secret_{test_suffix}"
        try:
            await secret_client.put_secret(secret_key, simple_secret_value)

            tags = [
                MetadataTag(key="environment", value="test", type="METADATA"),
                MetadataTag(key="type", value="api_key", type="METADATA"),
                MetadataTag(key="owner", value="integration_test", type="METADATA"),
            ]
            await secret_client.put_tag_for_secret(secret_key, tags)

            retrieved_tags = await secret_client.get_tags(secret_key)
            assert len(retrieved_tags) == 3
            tag_keys = [tag.key for tag in retrieved_tags]
            assert "environment" in tag_keys
            assert "type" in tag_keys
            assert "owner" in tag_keys

            tags_to_delete = [
                MetadataTag(key="owner", value="integration_test", type="METADATA")
            ]
            await secret_client.delete_tag_for_secret(secret_key, tags_to_delete)

            retrieved_tags_after_delete = await secret_client.get_tags(secret_key)
            remaining_tag_keys = [tag.key for tag in retrieved_tags_after_delete]
            assert "owner" not in remaining_tag_keys
            assert len(retrieved_tags_after_delete) == 2

        except Exception as e:
            print(f"Exception in test_secret_with_tags: {str(e)}")
            raise
        finally:
            try:
                await secret_client.delete_secret(secret_key)
            except Exception as e:
                print(f"Warning: Failed to cleanup secret {secret_key}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_secret_update(
        self,
        secret_client: OrkesSecretClient,
        test_suffix: str,
        simple_secret_value: str,
    ):
        secret_key = f"test_secret_update_{test_suffix}"
        try:
            initial_value = simple_secret_value
            await secret_client.put_secret(secret_key, initial_value)

            retrieved_value = await secret_client.get_secret(secret_key)

            # Handle case where secret is returned as JSON string
            if retrieved_value.startswith('"') and retrieved_value.endswith('"'):
                import json

                retrieved_value = json.loads(retrieved_value)

            assert retrieved_value == initial_value

            updated_value = "updated_secret_value_456"
            await secret_client.put_secret(secret_key, updated_value)

            updated_retrieved_value = await secret_client.get_secret(secret_key)

            # Handle case where secret is returned as JSON string
            if updated_retrieved_value.startswith(
                '"'
            ) and updated_retrieved_value.endswith('"'):
                import json

                updated_retrieved_value = json.loads(updated_retrieved_value)

            assert updated_retrieved_value == updated_value

        except Exception as e:
            print(f"Exception in test_secret_update: {str(e)}")
            raise
        finally:
            try:
                await secret_client.delete_secret(secret_key)
            except Exception as e:
                print(f"Warning: Failed to cleanup secret {secret_key}: {str(e)}")

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_complex_secret_management_flow(
        self, secret_client: OrkesSecretClient, test_suffix: str
    ):
        created_resources = {"secrets": []}

        try:
            secret_types = {
                "api_key": "sk-1234567890abcdef",
                "database_password": "db_password_secure_123",
                "redis_password": "redis_secret_456",
                "jwt_secret": "jwt_secret_key_789",
                "encryption_key": "encryption_key_abc123",
            }

            for secret_type, secret_value in secret_types.items():
                secret_key = f"complex_{secret_type}_{test_suffix}"
                await secret_client.put_secret(secret_key, secret_value)
                created_resources["secrets"].append(secret_key)

                tags = [
                    MetadataTag(key="type", value=secret_type, type="METADATA"),
                    MetadataTag(key="environment", value="test", type="METADATA"),
                    MetadataTag(key="owner", value="integration_test", type="METADATA"),
                ]
                await secret_client.put_tag_for_secret(secret_key, tags)

            all_secrets = await secret_client.list_all_secret_names()
            for secret_key in created_resources["secrets"]:
                assert (
                    secret_key in all_secrets
                ), f"Secret {secret_key} not found in list"

            for secret_type, secret_value in secret_types.items():
                secret_key = f"complex_{secret_type}_{test_suffix}"
                retrieved_value = await secret_client.get_secret(secret_key)

                # Handle case where secret is returned as JSON string
                if retrieved_value.startswith('"') and retrieved_value.endswith('"'):
                    import json

                    retrieved_value = json.loads(retrieved_value)

                assert retrieved_value == secret_value

                retrieved_tags = await secret_client.get_tags(secret_key)
                tag_keys = [tag.key for tag in retrieved_tags]
                assert "type" in tag_keys
                assert "environment" in tag_keys
                assert "owner" in tag_keys

            bulk_secrets = []
            for i in range(5):
                secret_key = f"bulk_secret_{i}_{test_suffix}"
                secret_value = f"bulk_value_{i}_{uuid.uuid4()}"
                await secret_client.put_secret(secret_key, secret_value)
                bulk_secrets.append(secret_key)
                created_resources["secrets"].append(secret_key)

            all_secrets_after_bulk = await secret_client.list_all_secret_names()
            for secret_key in bulk_secrets:
                assert (
                    secret_key in all_secrets_after_bulk
                ), f"Bulk secret {secret_key} not found in list"

            accessible_secrets = (
                await secret_client.list_secrets_that_user_can_grant_access_to()
            )
            assert isinstance(accessible_secrets, list)

            for secret_type in ["api_key", "database_password"]:
                secret_key = f"complex_{secret_type}_{test_suffix}"
                exists = await secret_client.secret_exists(secret_key)
                assert exists is True

        except Exception as e:
            print(f"Exception in test_complex_secret_management_flow: {str(e)}")
            raise
        finally:
            await self._perform_comprehensive_cleanup(secret_client, created_resources)

    async def _perform_comprehensive_cleanup(
        self, secret_client: OrkesSecretClient, created_resources: dict
    ):
        cleanup_enabled = os.getenv("CONDUCTOR_TEST_CLEANUP", "true").lower() == "true"
        if not cleanup_enabled:
            return

        for secret_key in created_resources["secrets"]:
            try:
                await secret_client.delete_secret(secret_key)
            except Exception as e:
                print(f"Warning: Failed to delete secret {secret_key}: {str(e)}")

        remaining_secrets = []
        for secret_key in created_resources["secrets"]:
            try:
                exists = await secret_client.secret_exists(secret_key)
                if exists:
                    remaining_secrets.append(secret_key)
            except ApiException as e:
                if e.status == 404:
                    pass
                else:
                    remaining_secrets.append(secret_key)
            except Exception:
                remaining_secrets.append(secret_key)

        if remaining_secrets:
            print(
                f"Warning: {len(remaining_secrets)} secrets could not be verified as deleted: {remaining_secrets}"
            )

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_secret_validated_methods(
        self, secret_client: OrkesSecretClient, test_suffix: str
    ):
        """Test validated secret methods."""
        secret_key = f"validated_secret_{test_suffix}"
        secret_value = "validated_secret_value"

        try:
            await secret_client.put_secret_validated(secret_key, secret_value)

            exists = await secret_client.secret_exists_validated(secret_key)
            assert exists is True

            has_secret = await secret_client.has_secret_validated(secret_key)
            assert has_secret is True

            retrieved_value = await secret_client.get_secret(secret_key)
            assert retrieved_value == '"validated_secret_value"'

            new_value = "updated_secret_value"
            await secret_client.update_secret_validated(secret_key, new_value)

            await secret_client.delete_secret_validated(secret_key)

            exists_after_delete = await secret_client.secret_exists_validated(secret_key)
            assert exists_after_delete is False
        except Exception as e:
            print(f"Exception in test_secret_validated_methods: {str(e)}")
            raise
        finally:
            try:
                await secret_client.delete_secret_validated(secret_key)
            except Exception:
                pass

    @pytest.mark.v5_2_6
    @pytest.mark.v4_1_73
    @pytest.mark.asyncio
    async def test_cache_validated_methods(self, secret_client: OrkesSecretClient):
        """Test validated cache methods."""
        try:
            await secret_client.clear_local_cache_validated()
            await secret_client.clear_redis_cache_validated()
        except Exception as e:
            print(f"Cache operations may not be supported: {str(e)}")
