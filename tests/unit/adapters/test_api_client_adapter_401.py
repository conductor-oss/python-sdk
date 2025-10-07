import pytest
from unittest.mock import Mock, patch

from conductor.client.http.api_client import ApiClient
from conductor.client.configuration.configuration import Configuration
from conductor.client.codegen.rest import AuthorizationException


class TestApiClientAdapter401Policy:
    def test_init_with_401_configuration(self):
        config = Configuration(
            auth_401_max_attempts=3,
            auth_401_base_delay_ms=500.0,
            auth_401_max_delay_ms=5000.0,
            auth_401_jitter_percent=0.1,
            auth_401_stop_behavior="stop_worker"
        )
        
        adapter = ApiClient(configuration=config)
        
        assert adapter.auth_401_handler.policy.max_attempts == 3
        assert adapter.auth_401_handler.policy.base_delay_ms == 500.0
        assert adapter.auth_401_handler.policy.max_delay_ms == 5000.0
        assert adapter.auth_401_handler.policy.jitter_percent == 0.1
        assert adapter.auth_401_handler.policy.stop_behavior == "stop_worker"

    def test_init_with_default_401_configuration(self):
        config = Configuration()
        adapter = ApiClient(configuration=config)
        
        assert adapter.auth_401_handler.policy.max_attempts == 6
        assert adapter.auth_401_handler.policy.base_delay_ms == 1000.0
        assert adapter.auth_401_handler.policy.max_delay_ms == 60000.0
        assert adapter.auth_401_handler.policy.jitter_percent == 0.2
        assert adapter.auth_401_handler.policy.stop_behavior == "stop_worker"

    @patch('conductor.client.adapters.api_client_adapter.time.sleep')
    def test_call_api_401_auth_dependent_retry(self, mock_sleep):
        config = Configuration(auth_401_max_attempts=2)
        adapter = ApiClient(configuration=config)
        
        # Mock successful response after retry
        mock_response = Mock()
        adapter._ApiClientAdapter__call_api_no_retry = Mock(side_effect=[
            AuthorizationException(status=401, reason="Unauthorized"),
            mock_response
        ])
        adapter._ApiClientAdapter__force_refresh_auth_token = Mock()
        
        result = adapter._ApiClientAdapter__call_api(
            resource_path="/workflow/start",
            method="POST"
        )
        
        assert result == mock_response
        assert adapter._ApiClientAdapter__call_api_no_retry.call_count == 2
        adapter._ApiClientAdapter__force_refresh_auth_token.assert_called_once()
        mock_sleep.assert_called_once()

    @patch('conductor.client.adapters.api_client_adapter.time.sleep')
    def test_call_api_401_auth_dependent_max_attempts(self, mock_sleep):
        config = Configuration(auth_401_max_attempts=1)
        adapter = ApiClient(configuration=config)
        
        # Mock 401 exception that should not be retried
        auth_exception = AuthorizationException(status=401, reason="Unauthorized")
        adapter._ApiClientAdapter__call_api_no_retry = Mock(side_effect=auth_exception)
        adapter._ApiClientAdapter__force_refresh_auth_token = Mock()
        
        with pytest.raises(AuthorizationException):
            adapter._ApiClientAdapter__call_api(
                resource_path="/workflow/start",
                method="POST"
            )
        
        # Should not retry or refresh token
        assert adapter._ApiClientAdapter__call_api_no_retry.call_count == 1
        adapter._ApiClientAdapter__force_refresh_auth_token.assert_not_called()

    def test_call_api_401_non_auth_dependent(self):
        config = Configuration()
        adapter = ApiClient(configuration=config)
        
        # Mock 401 exception for non-auth-dependent call
        auth_exception = AuthorizationException(status=401, reason="Unauthorized")
        auth_exception._error_code = 'EXPIRED_TOKEN'
        adapter._ApiClientAdapter__call_api_no_retry = Mock(side_effect=auth_exception)
        adapter._ApiClientAdapter__force_refresh_auth_token = Mock()
        
        # Should use original behavior (single retry)
        mock_response = Mock()
        adapter._ApiClientAdapter__call_api_no_retry.side_effect = [auth_exception, mock_response]
        
        result = adapter._ApiClientAdapter__call_api(
            resource_path="/token",
            method="POST"
        )
        
        assert result == mock_response
        assert adapter._ApiClientAdapter__call_api_no_retry.call_count == 2
        adapter._ApiClientAdapter__force_refresh_auth_token.assert_called_once()

    def test_call_api_403_error_not_affected_by_401_policy(self):
        config = Configuration()
        adapter = ApiClient(configuration=config)
        
        # Mock 403 exception (should not trigger 401 policy)
        auth_exception = AuthorizationException(status=403, reason="Forbidden")
        adapter._ApiClientAdapter__call_api_no_retry = Mock(side_effect=auth_exception)
        
        with pytest.raises(AuthorizationException):
            adapter._ApiClientAdapter__call_api(
                resource_path="/workflow/start",
                method="POST"
            )
        
        # Should not retry or refresh token
        assert adapter._ApiClientAdapter__call_api_no_retry.call_count == 1

    def test_call_api_successful_call_resets_401_counters(self):
        config = Configuration()
        adapter = ApiClient(configuration=config)
        
        # Mock successful response
        mock_response = Mock()
        adapter._ApiClientAdapter__call_api_no_retry = Mock(return_value=mock_response)
        
        result = adapter._ApiClientAdapter__call_api(
            resource_path="/workflow/start",
            method="POST"
        )
        
        assert result == mock_response
        # Verify that successful call resets 401 attempt counters
        assert adapter.auth_401_handler.policy.get_attempt_count("/workflow/start") == 0

    def test_call_api_401_policy_tracks_attempts_per_endpoint(self):
        config = Configuration(auth_401_max_attempts=2)
        adapter = ApiClient(configuration=config)
        
        # Mock 401 exceptions for different endpoints
        auth_exception = AuthorizationException(status=401, reason="Unauthorized")
        adapter._ApiClientAdapter__call_api_no_retry = Mock(side_effect=auth_exception)
        adapter._ApiClientAdapter__force_refresh_auth_token = Mock()
        
        # First endpoint - should retry
        with pytest.raises(AuthorizationException):
            adapter._ApiClientAdapter__call_api(
                resource_path="/workflow/start",
                method="POST"
            )
        
        # Second endpoint - should also retry (independent tracking)
        with pytest.raises(AuthorizationException):
            adapter._ApiClientAdapter__call_api(
                resource_path="/task/poll",
                method="GET"
            )
        
        # Each endpoint should have its own attempt count
        assert adapter.auth_401_handler.policy.get_attempt_count("/workflow/start") == 1
        assert adapter.auth_401_handler.policy.get_attempt_count("/task/poll") == 1

    @patch('conductor.client.adapters.api_client_adapter.logger')
    def test_call_api_401_logging(self, mock_logger):
        config = Configuration(auth_401_max_attempts=1)
        adapter = ApiClient(configuration=config)
        
        auth_exception = AuthorizationException(status=401, reason="Unauthorized")
        adapter._ApiClientAdapter__call_api_no_retry = Mock(side_effect=auth_exception)
        
        with pytest.raises(AuthorizationException):
            adapter._ApiClientAdapter__call_api(
                resource_path="/workflow/start",
                method="POST"
            )
        
        # Should log error about max attempts reached
        mock_logger.error.assert_called()

    def test_call_api_401_non_auth_endpoints(self):
        config = Configuration()
        adapter = ApiClient(configuration=config)
        
        auth_exception = AuthorizationException(status=401, reason="Unauthorized")
        auth_exception._error_code = 'EXPIRED_TOKEN'
        adapter._ApiClientAdapter__call_api_no_retry = Mock(side_effect=auth_exception)
        adapter._ApiClientAdapter__force_refresh_auth_token = Mock()
        
        # Test non-auth-dependent endpoints
        non_auth_endpoints = [
            "/token",
            "/auth/login",
            "/health",
            "/status"
        ]
        
        for endpoint in non_auth_endpoints:
            # Should use original behavior (single retry)
            mock_response = Mock()
            adapter._ApiClientAdapter__call_api_no_retry.side_effect = [auth_exception, mock_response]
            
            result = adapter._ApiClientAdapter__call_api(
                resource_path=endpoint,
                method="POST"
            )
            
            assert result == mock_response
            # Should not have 401 policy applied
            assert adapter.auth_401_handler.policy.get_attempt_count(endpoint) == 0
