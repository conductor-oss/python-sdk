import asyncio

import pytest
from unittest.mock import Mock, patch, AsyncMock

from conductor.asyncio_client.adapters.api_client_adapter import ApiClientAdapter
from conductor.asyncio_client.configuration import Configuration


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

    @pytest.mark.asyncio
    @patch("conductor.asyncio_client.adapters.api_client_adapter.asyncio.sleep")
    @patch("conductor.asyncio_client.adapters.api_client_adapter.time.time")
    async def test_call_api_401_concurrent_requests_race_condition(
        self, mock_time, mock_sleep
    ):
        mock_sleep.return_value = None
        config = Configuration(auth_401_max_attempts=3, auth_token_ttl_min=1)
        adapter = ApiClientAdapter(configuration=config)

        mock_response_401_first = Mock()
        mock_response_401_first.status = 401
        mock_response_success = Mock()
        mock_response_success.status = 200

        call_count = 0

        async def mock_request_side_effect(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response_401_first
            return mock_response_success

        refresh_count = 0

        async def mock_refresh_token():
            nonlocal refresh_count
            refresh_count += 1
            await asyncio.sleep(0.01)
            adapter.configuration._http_config.api_key["api_key"] = "refreshed_token"
            adapter.configuration.token_update_time = 1000.0
            mock_time.return_value = 1001.0
            return "refreshed_token"

        adapter.rest_client.request = AsyncMock(side_effect=mock_request_side_effect)
        adapter.refresh_authorization_token = AsyncMock(side_effect=mock_refresh_token)
        adapter.configuration._http_config.api_key["api_key"] = ""
        adapter.configuration.token_update_time = 0
        mock_time.return_value = 100.0

        tasks = []
        for _ in range(3):
            task = adapter.call_api(
                method="POST",
                url="http://localhost:8080/api/workflow/start",
                header_params={"X-Authorization": "old_token"},
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        for result in results:
            assert result.status == 200

        assert refresh_count == 1

    @pytest.mark.asyncio
    @patch("conductor.asyncio_client.adapters.api_client_adapter.asyncio.sleep")
    @patch("conductor.asyncio_client.adapters.api_client_adapter.time.time")
    async def test_call_api_401_token_already_refreshed_by_another_coroutine(
        self, mock_time, mock_sleep
    ):
        mock_sleep.return_value = None
        config = Configuration(auth_401_max_attempts=3, auth_token_ttl_min=1)
        adapter = ApiClientAdapter(configuration=config)

        mock_response_401 = Mock()
        mock_response_401.status = 401
        mock_response_success = Mock()
        mock_response_success.status = 200

        first_call = True

        async def mock_refresh_token():
            adapter.configuration._http_config.api_key["api_key"] = "refreshed_token"
            adapter.configuration.token_update_time = 1000.0
            mock_time.return_value = 1001.0
            return "refreshed_token"

        async def mock_request_side_effect(*_args, **_kwargs):
            nonlocal first_call
            if first_call:
                first_call = False
                return mock_response_401
            return mock_response_success

        adapter.rest_client.request = AsyncMock(side_effect=mock_request_side_effect)
        adapter.refresh_authorization_token = AsyncMock(side_effect=mock_refresh_token)

        mock_time.return_value = 100.0
        adapter.configuration._http_config.api_key["api_key"] = ""
        adapter.configuration.token_update_time = 0

        result = await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "old_token"},
        )

        assert result.status == 200
        adapter.refresh_authorization_token.assert_called_once()

        first_call = True
        adapter.rest_client.request = AsyncMock(side_effect=mock_request_side_effect)

        result2 = await adapter.call_api(
            method="POST",
            url="http://localhost:8080/api/workflow/start",
            header_params={"X-Authorization": "old_token"},
        )

        assert result2.status == 200
        adapter.refresh_authorization_token.assert_called_once()
