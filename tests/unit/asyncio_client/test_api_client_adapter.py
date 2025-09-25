import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from conductor.asyncio_client.adapters.api_client_adapter import ApiClientAdapter
from conductor.asyncio_client.configuration import Configuration
from conductor.asyncio_client.http.exceptions import ApiException
from conductor.asyncio_client.http.api_response import ApiResponse


@pytest.fixture
def mock_config():
    config = Configuration()
    config.host = "http://test.com"
    config.auth_key = "test_key"
    config.auth_secret = "test_secret"
    return config


@pytest.fixture
def adapter(mock_config):
    client_adapter = ApiClientAdapter()
    client_adapter.configuration = mock_config
    client_adapter.rest_client = AsyncMock()
    return client_adapter


def test_get_default():
    ApiClientAdapter._default = None
    instance1 = ApiClientAdapter.get_default()
    instance2 = ApiClientAdapter.get_default()
    assert instance1 is instance2
    assert isinstance(instance1, ApiClientAdapter)


@pytest.mark.asyncio
async def test_call_api_success(adapter):
    mock_response = MagicMock()
    mock_response.status = 200
    adapter.rest_client.request = AsyncMock(return_value=mock_response)

    result = await adapter.call_api("GET", "http://test.com/api")

    assert result == mock_response
    adapter.rest_client.request.assert_called_once()


@pytest.mark.asyncio
async def test_call_api_401_retry(adapter):
    mock_response = MagicMock()
    mock_response.status = 401
    adapter.rest_client.request = AsyncMock(return_value=mock_response)
    adapter.refresh_authorization_token = AsyncMock(return_value="new_token")

    result = await adapter.call_api(
        "GET", "http://test.com/api", {"X-Authorization": "old_token"}
    )

    assert result == mock_response
    assert adapter.rest_client.request.call_count == 2
    assert adapter.refresh_authorization_token.called


@pytest.mark.asyncio
async def test_call_api_401_token_endpoint_no_retry(adapter):
    mock_response = MagicMock()
    mock_response.status = 401
    adapter.rest_client.request = AsyncMock(return_value=mock_response)
    adapter.refresh_authorization_token = AsyncMock()

    result = await adapter.call_api("POST", "http://test.com/token")

    assert result == mock_response
    adapter.rest_client.request.assert_called_once()
    adapter.refresh_authorization_token.assert_not_called()


@pytest.mark.asyncio
async def test_call_api_exception(adapter):
    adapter.rest_client.request = AsyncMock(
        side_effect=ApiException(status=500, reason="Server Error")
    )

    with pytest.raises(ApiException):
        await adapter.call_api("GET", "http://test.com/api")


def test_response_deserialize_success(adapter):
    mock_response = MagicMock()
    mock_response.data = b'{"test": "data"}'
    mock_response.status = 200
    mock_response.getheader.return_value = "application/json; charset=utf-8"
    mock_response.getheaders.return_value = {"content-type": "application/json"}

    response_types_map = {"200": "object"}
    adapter.deserialize = MagicMock(return_value={"test": "data"})

    result = adapter.response_deserialize(mock_response, response_types_map)

    assert isinstance(result, ApiResponse)
    assert result.status_code == 200
    assert result.data == {"test": "data"}


def test_response_deserialize_bytearray(adapter):
    mock_response = MagicMock()
    mock_response.data = b"binary data"
    mock_response.status = 200
    mock_response.getheaders.return_value = {}

    response_types_map = {"200": "bytearray"}

    result = adapter.response_deserialize(mock_response, response_types_map)

    assert result.data == b"binary data"


def test_response_deserialize_file(adapter):
    mock_response = MagicMock()
    mock_response.data = b"file content"
    mock_response.status = 200
    mock_response.getheaders.return_value = {}

    response_types_map = {"200": "file"}
    adapter._ApiClientAdapter__deserialize_file = MagicMock(return_value="file_object")

    result = adapter.response_deserialize(mock_response, response_types_map)

    assert result.data == "file_object"


def test_response_deserialize_with_xx_status(adapter):
    mock_response = MagicMock()
    mock_response.data = b'{"test": "data"}'
    mock_response.status = 201
    mock_response.getheader.return_value = "application/json; charset=utf-8"
    mock_response.getheaders.return_value = {"content-type": "application/json"}

    response_types_map = {"2XX": "object"}
    adapter.deserialize = MagicMock(return_value={"test": "data"})

    result = adapter.response_deserialize(mock_response, response_types_map)

    assert result.status_code == 201


def test_response_deserialize_error_status(adapter):
    mock_response = MagicMock()
    mock_response.data = b'{"error": "message"}'
    mock_response.status = 400
    mock_response.getheader.return_value = "application/json; charset=utf-8"
    mock_response.getheaders.return_value = {"content-type": "application/json"}

    response_types_map = {"400": "object"}
    adapter.deserialize = MagicMock(return_value={"error": "message"})

    with pytest.raises(ApiException):
        adapter.response_deserialize(mock_response, response_types_map)


def test_response_deserialize_no_data_assertion(adapter):
    mock_response = MagicMock()
    mock_response.data = None

    with pytest.raises(AssertionError) as exc_info:
        adapter.response_deserialize(mock_response, {})

    assert "RESTResponse.read() must be called" in str(exc_info.value)


@pytest.mark.asyncio
async def test_refresh_authorization_token(adapter):
    mock_token_response = {"token": "new_token_value"}
    adapter.obtain_new_token = AsyncMock(return_value=mock_token_response)

    result = await adapter.refresh_authorization_token()

    assert result == "new_token_value"
    assert adapter.configuration.api_key["api_key"] == "new_token_value"


@pytest.mark.asyncio
async def test_obtain_new_token(adapter):
    mock_response = MagicMock()
    mock_response.data = b'{"token": "test_token"}'
    mock_response.read = AsyncMock()
    adapter.call_api = AsyncMock(return_value=mock_response)
    adapter.param_serialize = MagicMock(
        return_value=(
            "POST",
            "/token",
            {},
            {"key_id": "test_key", "key_secret": "test_secret"},
        )
    )

    result = await adapter.obtain_new_token()

    assert result == {"token": "test_token"}
    adapter.call_api.assert_called_once()
    mock_response.read.assert_called_once()


@pytest.mark.asyncio
async def test_obtain_new_token_with_patch():
    with patch(
        "conductor.asyncio_client.adapters.api_client_adapter.GenerateTokenRequest"
    ) as mock_generate_token:
        mock_token_request = MagicMock()
        mock_token_request.to_dict.return_value = {
            "key_id": "test_key",
            "key_secret": "test_secret",
        }
        mock_generate_token.return_value = mock_token_request

        client_adapter = ApiClientAdapter()
        client_adapter.configuration = MagicMock()
        client_adapter.configuration.auth_key = "test_key"
        client_adapter.configuration.auth_secret = "test_secret"
        client_adapter.param_serialize = MagicMock(
            return_value=("POST", "/token", {}, {})
        )

        mock_response = MagicMock()
        mock_response.data = b'{"token": "test_token"}'
        mock_response.read = AsyncMock()
        client_adapter.call_api = AsyncMock(return_value=mock_response)

        result = await client_adapter.obtain_new_token()

        assert result == {"token": "test_token"}
        mock_generate_token.assert_called_once_with(
            key_id="test_key", key_secret="test_secret"
        )


def test_response_deserialize_encoding_detection(adapter):
    mock_response = MagicMock()
    mock_response.data = b'{"test": "data"}'
    mock_response.status = 200
    mock_response.getheader.return_value = "application/json; charset=iso-8859-1"
    mock_response.getheaders.return_value = {"content-type": "application/json"}

    response_types_map = {"200": "object"}
    adapter.deserialize = MagicMock(return_value={"test": "data"})

    result = adapter.response_deserialize(mock_response, response_types_map)

    assert result.status_code == 200
    adapter.deserialize.assert_called_once()


def test_response_deserialize_no_content_type(adapter):
    mock_response = MagicMock()
    mock_response.data = b'{"test": "data"}'
    mock_response.status = 200
    mock_response.getheader.return_value = None
    mock_response.getheaders.return_value = {}

    response_types_map = {"200": "object"}
    adapter.deserialize = MagicMock(return_value={"test": "data"})

    result = adapter.response_deserialize(mock_response, response_types_map)

    assert result.status_code == 200
    adapter.deserialize.assert_called_once()


def test_response_deserialize_no_match_content_type(adapter):
    mock_response = MagicMock()
    mock_response.data = b'{"test": "data"}'
    mock_response.status = 200
    mock_response.getheader.return_value = "application/json"
    mock_response.getheaders.return_value = {}

    response_types_map = {"200": "object"}
    adapter.deserialize = MagicMock(return_value={"test": "data"})

    result = adapter.response_deserialize(mock_response, response_types_map)

    assert result.status_code == 200
    adapter.deserialize.assert_called_once()
