import pytest
from unittest.mock import MagicMock, patch
from conductor.client.adapters.api_client_adapter import ApiClientAdapter
from conductor.client.codegen.rest import AuthorizationException, ApiException


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.host = "http://test.com"
    return config


@pytest.fixture
def api_adapter(mock_config):
    client_adapter = ApiClientAdapter()
    client_adapter.configuration = mock_config
    return client_adapter


def test_call_api_success(api_adapter):
    mock_response = MagicMock()
    api_adapter._ApiClientAdapter__call_api_no_retry = MagicMock(
        return_value=mock_response
    )

    result = api_adapter._ApiClientAdapter__call_api(
        resource_path="/test",
        method="GET",
        path_params=None,
        query_params=None,
        header_params=None,
        body=None,
        post_params=None,
        files=None,
        response_type=None,
        auth_settings=None,
        _return_http_data_only=None,
        collection_formats=None,
        _preload_content=True,
        _request_timeout=None,
    )

    assert result == mock_response
    api_adapter._ApiClientAdapter__call_api_no_retry.assert_called_once()


def test_call_api_authorization_exception_expired_token(api_adapter):
    mock_response = MagicMock()
    mock_auth_exception = AuthorizationException(status=401, reason="Unauthorized")
    mock_auth_exception._error_code = "EXPIRED_TOKEN"
    api_adapter._ApiClientAdapter__call_api_no_retry = MagicMock(
        side_effect=[mock_auth_exception, mock_response]
    )
    api_adapter._ApiClientAdapter__force_refresh_auth_token = MagicMock()

    with patch("conductor.client.adapters.api_client_adapter.logger") as mock_logger:
        result = api_adapter._ApiClientAdapter__call_api(
            resource_path="/test",
            method="GET",
            path_params=None,
            query_params=None,
            header_params=None,
            body=None,
            post_params=None,
            files=None,
            response_type=None,
            auth_settings=None,
            _return_http_data_only=None,
            collection_formats=None,
            _preload_content=True,
            _request_timeout=None,
        )

    assert result == mock_response
    assert api_adapter._ApiClientAdapter__call_api_no_retry.call_count == 2
    api_adapter._ApiClientAdapter__force_refresh_auth_token.assert_called_once()
    mock_logger.warning.assert_called_once()


def test_call_api_authorization_exception_invalid_token(api_adapter):
    mock_response = MagicMock()
    mock_auth_exception = AuthorizationException(status=401, reason="Unauthorized")
    mock_auth_exception._error_code = "INVALID_TOKEN"
    api_adapter._ApiClientAdapter__call_api_no_retry = MagicMock(
        side_effect=[mock_auth_exception, mock_response]
    )
    api_adapter._ApiClientAdapter__force_refresh_auth_token = MagicMock()

    with patch("conductor.client.adapters.api_client_adapter.logger") as mock_logger:
        result = api_adapter._ApiClientAdapter__call_api(
            resource_path="/test",
            method="GET",
            path_params=None,
            query_params=None,
            header_params=None,
            body=None,
            post_params=None,
            files=None,
            response_type=None,
            auth_settings=None,
            _return_http_data_only=None,
            collection_formats=None,
            _preload_content=True,
            _request_timeout=None,
        )

    assert result == mock_response
    assert api_adapter._ApiClientAdapter__call_api_no_retry.call_count == 2
    api_adapter._ApiClientAdapter__force_refresh_auth_token.assert_called_once()
    mock_logger.warning.assert_called_once()


def test_call_api_authorization_exception_other(api_adapter):
    mock_auth_exception = AuthorizationException(status=401, reason="Unauthorized")
    mock_auth_exception._error_code = "OTHER_ERROR"
    api_adapter._ApiClientAdapter__call_api_no_retry = MagicMock(
        side_effect=mock_auth_exception
    )

    with pytest.raises(AuthorizationException):
        api_adapter._ApiClientAdapter__call_api(
            resource_path="/test",
            method="GET",
            path_params=None,
            query_params=None,
            header_params=None,
            body=None,
            post_params=None,
            files=None,
            response_type=None,
            auth_settings=None,
            _return_http_data_only=None,
            collection_formats=None,
            _preload_content=True,
            _request_timeout=None,
        )


def test_call_api_exception(api_adapter):
    api_adapter._ApiClientAdapter__call_api_no_retry = MagicMock(
        side_effect=ApiException(status=500, reason="Server Error")
    )

    with patch("conductor.client.adapters.api_client_adapter.logger") as mock_logger:
        with pytest.raises(ApiException):
            api_adapter._ApiClientAdapter__call_api(
                resource_path="/test",
                method="GET",
                path_params=None,
                query_params=None,
                header_params=None,
                body=None,
                post_params=None,
                files=None,
                response_type=None,
                auth_settings=None,
                _return_http_data_only=None,
                collection_formats=None,
                _preload_content=True,
                _request_timeout=None,
            )

    mock_logger.error.assert_called_once()


def test_call_api_with_all_parameters(api_adapter):
    mock_response = MagicMock()
    api_adapter._ApiClientAdapter__call_api_no_retry = MagicMock(
        return_value=mock_response
    )

    result = api_adapter._ApiClientAdapter__call_api(
        resource_path="/test",
        method="POST",
        path_params={"id": "123"},
        query_params={"param": "value"},
        header_params={"Authorization": "Bearer token"},
        body={"data": "test"},
        post_params={"form": "data"},
        files={"file": "content"},
        response_type=dict,
        auth_settings=["api_key"],
        _return_http_data_only=True,
        collection_formats={"param": "csv"},
        _preload_content=False,
        _request_timeout=30,
    )

    assert result == mock_response
    api_adapter._ApiClientAdapter__call_api_no_retry.assert_called_once_with(
        resource_path="/test",
        method="POST",
        path_params={"id": "123"},
        query_params={"param": "value"},
        header_params={"Authorization": "Bearer token"},
        body={"data": "test"},
        post_params={"form": "data"},
        files={"file": "content"},
        response_type=dict,
        auth_settings=["api_key"],
        _return_http_data_only=True,
        collection_formats={"param": "csv"},
        _preload_content=False,
        _request_timeout=30,
    )


def test_call_api_debug_logging(api_adapter):
    api_adapter._ApiClientAdapter__call_api_no_retry = MagicMock(
        return_value=MagicMock()
    )

    with patch("conductor.client.adapters.api_client_adapter.logger") as mock_logger:
        api_adapter._ApiClientAdapter__call_api(
            resource_path="/test",
            method="GET",
            header_params={"Authorization": "Bearer token"},
        )

    mock_logger.debug.assert_called_once()
    call_args = mock_logger.debug.call_args[0]
    assert (
        call_args[0] == "HTTP request method: %s; resource_path: %s; header_params: %s"
    )
    assert call_args[1] == "GET"
    assert call_args[2] == "/test"
    assert call_args[3] == {"Authorization": "Bearer token"}
