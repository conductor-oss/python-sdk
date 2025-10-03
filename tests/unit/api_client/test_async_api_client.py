import asyncio
import time

import pytest

from conductor.asyncio_client.adapters import ApiClient
from conductor.asyncio_client.configuration.configuration import Configuration
from conductor.asyncio_client.http.rest import RESTResponse


@pytest.fixture
def api_client():
    configuration = Configuration(
        server_url="http://localhost:8080/api",
        auth_key="test_key",
        auth_secret="test_secret",
    )
    return ApiClient(configuration)


@pytest.fixture
def mock_success_response(mocker):
    response = mocker.Mock(spec=RESTResponse)
    response.status = 200
    response.data = b'{"token": "test_token"}'
    response.read = mocker.Mock()
    return response


@pytest.fixture
def mock_401_response(mocker):
    response = mocker.Mock(spec=RESTResponse)
    response.status = 401
    response.data = b'{"message":"Token cannot be null or empty","error":"INVALID_TOKEN","timestamp":1758039192168}'
    response.read = mocker.AsyncMock()
    return response


@pytest.mark.asyncio
async def test_refresh_authorization_token_called_on_invalid_token(
    mocker, api_client, mock_401_response, mock_success_response
):
    api_client.configuration._http_config.api_key = {}

    api_client.rest_client = mocker.AsyncMock()
    api_client.rest_client.request.side_effect = [
        mock_401_response,
        mock_success_response,
    ]

    mock_refresh = mocker.patch.object(
        api_client, "refresh_authorization_token", new_callable=mocker.AsyncMock
    )
    mock_refresh.return_value = "new_token"

    mock_obtain = mocker.patch.object(
        api_client, "obtain_new_token", new_callable=mocker.AsyncMock
    )
    mock_obtain.return_value = {"token": "new_token"}

    await api_client.call_api(
        method="GET", url="http://localhost:8080/api/test", header_params={}
    )

    mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_authorization_token_called_on_expired_token(
    mocker, api_client, mock_401_response, mock_success_response
):
    current_time = time.time()
    api_client.configuration.token_update_time = current_time - 3600
    api_client.configuration.auth_token_ttl_sec = 1800
    api_client.configuration._http_config.api_key = {"api_key": "old_token"}

    api_client.rest_client = mocker.AsyncMock()
    api_client.rest_client.request.side_effect = [
        mock_401_response,
        mock_success_response,
    ]

    mock_refresh = mocker.patch.object(
        api_client, "refresh_authorization_token", new_callable=mocker.AsyncMock
    )
    mock_refresh.return_value = "new_token"

    mock_obtain = mocker.patch.object(
        api_client, "obtain_new_token", new_callable=mocker.AsyncMock
    )
    mock_obtain.return_value = {"token": "new_token"}

    await api_client.call_api(
        method="GET", url="http://localhost:8080/api/test", header_params={}
    )

    mock_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_token_lock_prevents_concurrent_refresh(
    mocker, api_client, mock_401_response, mock_success_response
):
    api_client.configuration._http_config.api_key = {}

    refresh_calls = []

    async def mock_refresh():
        refresh_calls.append(time.time())
        await asyncio.sleep(0.1)
        return "new_token"

    mocker.patch.object(
        api_client, "refresh_authorization_token", side_effect=mock_refresh
    )

    mock_obtain = mocker.patch.object(
        api_client, "obtain_new_token", new_callable=mocker.AsyncMock
    )
    mock_obtain.return_value = {"token": "new_token"}

    api_client.rest_client = mocker.AsyncMock()
    api_client.rest_client.request.side_effect = [
        mock_401_response,
        mock_success_response,
        mock_401_response,
        mock_success_response,
    ]

    tasks = [
        api_client.call_api(
            method="GET",
            url="http://localhost:8080/api/test1",
            header_params={},
        ),
        api_client.call_api(
            method="GET",
            url="http://localhost:8080/api/test2",
            header_params={},
        ),
    ]

    await asyncio.gather(*tasks)

    assert len(refresh_calls) == 1


@pytest.mark.asyncio
async def test_no_refresh_when_token_valid_and_not_expired(
    mocker, api_client, mock_success_response
):
    current_time = time.time()
    api_client.configuration.token_update_time = current_time - 100
    api_client.configuration.auth_token_ttl_sec = 1800
    api_client.configuration._http_config.api_key = {"api_key": "valid_token"}

    api_client.rest_client = mocker.AsyncMock()
    api_client.rest_client.request.return_value = mock_success_response

    mock_refresh = mocker.patch.object(
        api_client, "refresh_authorization_token", new_callable=mocker.AsyncMock
    )

    await api_client.call_api(
        method="GET", url="http://localhost:8080/api/test", header_params={}
    )

    mock_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_no_refresh_for_token_endpoint(mocker, api_client, mock_401_response):
    api_client.configuration._http_config.api_key = {}

    api_client.rest_client = mocker.AsyncMock()
    api_client.rest_client.request.return_value = mock_401_response

    mock_refresh = mocker.patch.object(
        api_client, "refresh_authorization_token", new_callable=mocker.AsyncMock
    )

    await api_client.call_api(
        method="POST", url="http://localhost:8080/api/token", header_params={}
    )

    mock_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_401_response_triggers_retry_with_new_token(
    mocker, api_client, mock_401_response, mock_success_response
):
    api_client.configuration._http_config.api_key = {}

    api_client.rest_client = mocker.AsyncMock()
    api_client.rest_client.request.side_effect = [
        mock_401_response,
        mock_success_response,
    ]

    mock_refresh = mocker.patch.object(
        api_client, "refresh_authorization_token", new_callable=mocker.AsyncMock
    )
    mock_refresh.return_value = "new_token"

    mock_obtain = mocker.patch.object(
        api_client, "obtain_new_token", new_callable=mocker.AsyncMock
    )
    mock_obtain.return_value = {"token": "new_token"}

    header_params = {}
    await api_client.call_api(
        method="GET",
        url="http://localhost:8080/api/test",
        header_params=header_params,
    )

    assert api_client.rest_client.request.call_count == 2

    second_call_args = api_client.rest_client.request.call_args_list[1]
    assert second_call_args[1]["headers"]["X-Authorization"] == "new_token"
