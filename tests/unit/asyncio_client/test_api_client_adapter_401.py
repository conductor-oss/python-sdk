import pytest
from unittest.mock import Mock, patch, AsyncMock

from conductor.asyncio_client.adapters.api_client_adapter import ApiClientAdapter
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.http import rest


class TestApiClientAdapter401Policy:
    def test_init_with_401_configuration(self):
        config = Configuration(
            auth_401_max_attempts=3,
            auth_401_base_delay_ms=500.0,
            auth_401_max_delay_ms=5000.0,
            auth_401_jitter_percent=0.1,
            auth_401_stop_behavior="stop_worker",
        )

        adapter = ApiClientAdapter(configuration=config)

        assert adapter.auth_401_handler.policy.max_attempts == 3
        assert adapter.auth_401_handler.policy.base_delay_ms == 500.0
        assert adapter.auth_401_handler.policy.max_delay_ms == 5000.0
        assert adapter.auth_401_handler.policy.jitter_percent == 0.1
        assert adapter.auth_401_handler.policy.stop_behavior == "stop_worker"

    def test_init_with_default_401_configuration(self):
        config = Configuration()
        adapter = ApiClientAdapter(configuration=config)

        assert adapter.auth_401_handler.policy.max_attempts == 6
        assert adapter.auth_401_handler.policy.base_delay_ms == 1000.0
        assert adapter.auth_401_handler.policy.max_delay_ms == 60000.0
        assert adapter.auth_401_handler.policy.jitter_percent == 0.2
        assert adapter.auth_401_handler.policy.stop_behavior == "stop_worker"

    @pytest.mark.asyncio
    @patch("conductor.asyncio_client.adapters.api_client_adapter.asyncio.sleep")
    async def test_call_api_401_auth_dependent_retry(self, mock_sleep):
        mock_sleep.return_value = None
        config = Configuration(auth_401_max_attempts=2)
        adapter = ApiClientAdapter(configuration=config)

        mock_response_401 = Mock()
        mock_response_401.status = 401
        mock_response_success = Mock()
        mock_response_success.status = 200

        adapter.rest_client.request = AsyncMock(
            side_effect=[mock_response_401, mock_response_success]
        )
        adapter.refresh_authorization_token = AsyncMock(return_value="new_token")

        result = await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "old_token"},
        )

        assert result == mock_response_success
        assert adapter.rest_client.request.call_count == 2
        adapter.refresh_authorization_token.assert_called_once()
        mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    @patch("conductor.asyncio_client.adapters.api_client_adapter.asyncio.sleep")
    async def test_call_api_401_auth_dependent_max_attempts(self, mock_sleep):
        mock_sleep.return_value = None
        config = Configuration(auth_401_max_attempts=1)
        adapter = ApiClientAdapter(configuration=config)

        mock_response_401 = Mock()
        mock_response_401.status = 401

        adapter.rest_client.request = AsyncMock(return_value=mock_response_401)
        adapter.refresh_authorization_token = AsyncMock(return_value="new_token")

        result = await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "old_token"},
        )

        assert result == mock_response_401
        assert adapter.rest_client.request.call_count == 1
        adapter.refresh_authorization_token.assert_not_called()
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_call_api_401_non_auth_dependent(self):
        config = Configuration()
        adapter = ApiClientAdapter(configuration=config)

        mock_response_401 = Mock()
        mock_response_401.status = 401

        adapter.rest_client.request = AsyncMock(return_value=mock_response_401)
        adapter.refresh_authorization_token = AsyncMock(return_value="new_token")

        result = await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/token",
            header_params={"X-Authorization": "old_token"},
        )

        assert result == mock_response_401
        assert adapter.rest_client.request.call_count == 1
        adapter.refresh_authorization_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_call_api_403_error_not_affected_by_401_policy(self):
        config = Configuration()
        adapter = ApiClientAdapter(configuration=config)

        mock_response_403 = Mock()
        mock_response_403.status = 403

        adapter.rest_client.request = AsyncMock(return_value=mock_response_403)

        result = await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "token"},
        )

        assert result == mock_response_403
        assert adapter.rest_client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_call_api_successful_call_resets_401_counters(self):
        config = Configuration()
        adapter = ApiClientAdapter(configuration=config)

        mock_response_success = Mock()
        mock_response_success.status = 200

        adapter.rest_client.request = AsyncMock(return_value=mock_response_success)

        result = await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "token"},
        )

        assert result == mock_response_success
        assert adapter.auth_401_handler.policy.get_attempt_count("/workflow/start") == 0

    @pytest.mark.asyncio
    async def test_call_api_401_policy_tracks_attempts_per_endpoint(self):
        config = Configuration(auth_401_max_attempts=2)
        adapter = ApiClientAdapter(configuration=config)

        mock_response_401 = Mock()
        mock_response_401.status = 401

        adapter.rest_client.request = AsyncMock(return_value=mock_response_401)
        adapter.refresh_authorization_token = AsyncMock(return_value="new_token")

        await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "token"},
        )

        await adapter.call_api(
            method="GET",
            url="http://localhost:8080/api/task/poll",
            header_params={"X-Authorization": "token"},
        )

        # With max_attempts=2, each endpoint will have 2 attempts (initial + 1 retry)
        assert adapter.auth_401_handler.policy.get_attempt_count("/workflow/start") == 2
        assert adapter.auth_401_handler.policy.get_attempt_count("/task/poll") == 2

    @pytest.mark.asyncio
    @patch("conductor.asyncio_client.adapters.api_client_adapter.logger")
    async def test_call_api_401_logging(self, mock_logger):
        config = Configuration(auth_401_max_attempts=1)
        adapter = ApiClientAdapter(configuration=config)

        mock_response_401 = Mock()
        mock_response_401.status = 401

        adapter.rest_client.request = AsyncMock(return_value=mock_response_401)

        await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "token"},
        )

        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_call_api_401_non_auth_endpoints(self):
        config = Configuration()
        adapter = ApiClientAdapter(configuration=config)

        mock_response_401 = Mock()
        mock_response_401.status = 401
        mock_response_success = Mock()
        mock_response_success.status = 200

        adapter.rest_client.request = AsyncMock(return_value=mock_response_401)
        adapter.refresh_authorization_token = AsyncMock(return_value="new_token")

        result = await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/token",
            header_params={"X-Authorization": "token"},
        )

        assert result == mock_response_401
        assert adapter.rest_client.request.call_count == 1
        adapter.refresh_authorization_token.assert_not_called()
        assert adapter.auth_401_handler.policy.get_attempt_count("/token") == 0

        non_auth_endpoints = ["/auth/login", "/health", "/status"]

        for endpoint in non_auth_endpoints:
            adapter.rest_client.request = AsyncMock(
                side_effect=[mock_response_401, mock_response_success]
            )
            adapter.refresh_authorization_token = AsyncMock(return_value="new_token")

            result = await adapter.call_api(
                method="POST",
                url=f"http://localhost:8080/api{endpoint}",
                header_params={"X-Authorization": "token"},
            )

            assert result == mock_response_success
            assert adapter.auth_401_handler.policy.get_attempt_count(endpoint) == 0

    @pytest.mark.asyncio
    @patch("conductor.asyncio_client.adapters.api_client_adapter.asyncio.sleep")
    async def test_call_api_401_exponential_backoff(self, mock_sleep):
        mock_sleep.return_value = None
        config = Configuration(auth_401_max_attempts=3, auth_401_base_delay_ms=1000.0)
        adapter = ApiClientAdapter(configuration=config)

        mock_response_success = Mock()
        mock_response_success.status = 200

        mock_response_401_1 = Mock()
        mock_response_401_1.status = 401
        mock_response_401_2 = Mock()
        mock_response_401_2.status = 401

        adapter.rest_client.request = AsyncMock(
            side_effect=[
                mock_response_401_1,
                mock_response_401_2,
                mock_response_success,
            ]
        )
        adapter.refresh_authorization_token = AsyncMock(return_value="new_token")

        result = await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "token"},
        )

        assert result.status == 200
        assert mock_sleep.call_count == 2

        first_delay = mock_sleep.call_args_list[0][0][0]
        second_delay = mock_sleep.call_args_list[1][0][0]

        assert 1.6 <= first_delay <= 2.4
        assert 3.2 <= second_delay <= 4.8
        assert second_delay > first_delay

    @pytest.mark.asyncio
    async def test_call_api_success_after_401_resets_counter(self):
        config = Configuration(auth_401_max_attempts=3)
        adapter = ApiClientAdapter(configuration=config)

        mock_response_401 = Mock()
        mock_response_401.status = 401
        mock_response_success = Mock()
        mock_response_success.status = 200

        adapter.rest_client.request = AsyncMock(
            side_effect=[mock_response_401, mock_response_success]
        )
        adapter.refresh_authorization_token = AsyncMock(return_value="new_token")

        await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "token"},
        )

        assert adapter.auth_401_handler.policy.get_attempt_count("/workflow/start") == 0

        adapter.rest_client.request = AsyncMock(
            side_effect=[mock_response_401, mock_response_success]
        )

        await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "token"},
        )

        assert adapter.auth_401_handler.policy.get_attempt_count("/workflow/start") == 0
