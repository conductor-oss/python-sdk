from unittest.mock import Mock, patch
import pytest
import httpx
from httpx import Response, RequestError, HTTPStatusError, TimeoutException

from conductor.client.adapters.rest_adapter import RESTResponse, RESTClientObjectAdapter
from conductor.client.codegen.rest import ApiException, AuthorizationException


def test_rest_response_initialization():
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b'{"test": "data"}'
    mock_response.text = '{"test": "data"}'
    mock_response.url = "https://example.com/api"
    mock_response.http_version = "HTTP/1.1"

    rest_response = RESTResponse(mock_response)

    assert rest_response.status == 200
    assert rest_response.reason == "OK"
    assert rest_response.headers == {"Content-Type": "application/json"}
    assert rest_response.data == b'{"test": "data"}'
    assert rest_response.text == '{"test": "data"}'
    assert rest_response.http_version == "HTTP/1.1"


def test_rest_response_getheaders():
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {"Content-Type": "application/json", "Server": "nginx"}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    rest_response = RESTResponse(mock_response)
    headers = rest_response.getheaders()

    assert headers == {"Content-Type": "application/json", "Server": "nginx"}


def test_rest_response_getheader():
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {"Content-Type": "application/json", "Server": "nginx"}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    rest_response = RESTResponse(mock_response)

    assert rest_response.getheader("Content-Type") == "application/json"
    assert rest_response.getheader("Server") == "nginx"
    assert rest_response.getheader("Non-Existent") is None
    assert rest_response.getheader("Non-Existent", "default") == "default"


def test_rest_response_is_http2():
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/2"

    rest_response = RESTResponse(mock_response)

    assert rest_response.is_http2() is True

    mock_response.http_version = "HTTP/1.1"
    assert rest_response.is_http2() is False


def test_rest_response_http_version_unknown():
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    del mock_response.http_version

    rest_response = RESTResponse(mock_response)

    assert rest_response.http_version == "Unknown"
    assert rest_response.is_http2() is False


def test_rest_client_object_adapter_initialization():
    adapter = RESTClientObjectAdapter()

    assert adapter.connection is not None
    assert isinstance(adapter.connection, httpx.Client)


def test_rest_client_object_adapter_initialization_with_connection():
    mock_connection = Mock(spec=httpx.Client)
    adapter = RESTClientObjectAdapter(connection=mock_connection)

    assert adapter.connection == mock_connection


def test_rest_client_object_adapter_close():
    mock_connection = Mock(spec=httpx.Client)
    adapter = RESTClientObjectAdapter(connection=mock_connection)

    adapter.close()
    mock_connection.close.assert_called_once()


def test_rest_client_object_adapter_close_no_connection():
    adapter = RESTClientObjectAdapter()
    adapter.connection = None

    adapter.close()


@patch("conductor.client.adapters.rest_adapter.logger")
def test_check_http2_support_success(mock_logger):
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/2"

    with patch.object(adapter, "GET", return_value=RESTResponse(mock_response)):
        result = adapter.check_http2_support("https://example.com")

        assert result is True
        mock_logger.info.assert_called()


@patch("conductor.client.adapters.rest_adapter.logger")
def test_check_http2_support_failure(mock_logger):
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter, "GET", return_value=RESTResponse(mock_response)):
        result = adapter.check_http2_support("https://example.com")

        assert result is False
        mock_logger.info.assert_called()


@patch("conductor.client.adapters.rest_adapter.logger")
def test_check_http2_support_exception(mock_logger):
    adapter = RESTClientObjectAdapter()

    with patch.object(adapter, "GET", side_effect=Exception("Connection failed")):
        result = adapter.check_http2_support("https://example.com")

        assert result is False
        mock_logger.error.assert_called()


def test_request_get_success():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        response = adapter.request("GET", "https://example.com")

        assert isinstance(response, RESTResponse)
        assert response.status == 200


def test_request_post_with_json_body():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 201
    mock_response.reason_phrase = "Created"
    mock_response.headers = {}
    mock_response.content = b'{"id": 123}'
    mock_response.text = '{"id": 123}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        response = adapter.request(
            "POST", "https://example.com", body={"name": "test", "value": 42}
        )

        assert isinstance(response, RESTResponse)
        assert response.status == 201


def test_request_post_with_string_body():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 201
    mock_response.reason_phrase = "Created"
    mock_response.headers = {}
    mock_response.content = b'{"id": 123}'
    mock_response.text = '{"id": 123}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        response = adapter.request("POST", "https://example.com", body="test string")

        assert isinstance(response, RESTResponse)
        assert response.status == 201


def test_request_post_with_bytes_body():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 201
    mock_response.reason_phrase = "Created"
    mock_response.headers = {}
    mock_response.content = b'{"id": 123}'
    mock_response.text = '{"id": 123}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        response = adapter.request("POST", "https://example.com", body=b"test bytes")

        assert isinstance(response, RESTResponse)
        assert response.status == 201


def test_request_with_query_params():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        response = adapter.request(
            "GET", "https://example.com", query_params={"page": 1, "limit": 10}
        )

        assert isinstance(response, RESTResponse)
        assert response.status == 200


def test_request_with_headers():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        response = adapter.request(
            "GET", "https://example.com", headers={"Authorization": "Bearer token"}
        )

        assert isinstance(response, RESTResponse)
        assert response.status == 200


def test_request_with_post_params():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        response = adapter.request(
            "POST",
            "https://example.com",
            post_params={"field1": "value1", "field2": "value2"},
        )

        assert isinstance(response, RESTResponse)
        assert response.status == 200


def test_request_with_custom_timeout():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        response = adapter.request("GET", "https://example.com", _request_timeout=30.0)

        assert isinstance(response, RESTResponse)
        assert response.status == 200


def test_request_with_tuple_timeout():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter.connection, "request", return_value=mock_response
    ) as mock_request:
        response = adapter.request(
            "GET", "https://example.com", _request_timeout=(5.0, 30.0)
        )

        assert isinstance(response, RESTResponse)
        assert response.status == 200

        call_args = mock_request.call_args
        timeout_arg = call_args[1]["timeout"]
        assert timeout_arg.connect == 5.0
        assert timeout_arg.read == 30.0


def test_request_authorization_error():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 401
    mock_response.reason_phrase = "Unauthorized"
    mock_response.headers = {}
    mock_response.content = b'{"error": "unauthorized"}'
    mock_response.text = '{"error": "unauthorized"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        with pytest.raises(AuthorizationException):
            adapter.request("GET", "https://example.com")


def test_request_forbidden_error():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 403
    mock_response.reason_phrase = "Forbidden"
    mock_response.headers = {}
    mock_response.content = b'{"error": "forbidden"}'
    mock_response.text = '{"error": "forbidden"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        with pytest.raises(AuthorizationException):
            adapter.request("GET", "https://example.com")


def test_request_http_error():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 404
    mock_response.reason_phrase = "Not Found"
    mock_response.headers = {}
    mock_response.content = b'{"error": "not found"}'
    mock_response.text = '{"error": "not found"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(adapter.connection, "request", return_value=mock_response):
        with pytest.raises(ApiException):
            adapter.request("GET", "https://example.com")


def test_request_http_status_error():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 500
    mock_response.reason_phrase = "Internal Server Error"
    mock_response.headers = {}
    mock_response.content = b'{"error": "server error"}'
    mock_response.text = '{"error": "server error"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    http_error = HTTPStatusError("Server Error", request=Mock(), response=mock_response)

    with patch.object(adapter.connection, "request", side_effect=http_error):
        with pytest.raises(ApiException):
            adapter.request("GET", "https://example.com")


def test_request_http_status_error_unauthorized():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 401
    mock_response.reason_phrase = "Unauthorized"
    mock_response.headers = {}
    mock_response.content = b'{"error": "unauthorized"}'
    mock_response.text = '{"error": "unauthorized"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    http_error = HTTPStatusError("Unauthorized", request=Mock(), response=mock_response)

    with patch.object(adapter.connection, "request", side_effect=http_error):
        with pytest.raises(AuthorizationException):
            adapter.request("GET", "https://example.com")


def test_request_connection_error():
    adapter = RESTClientObjectAdapter()

    with patch.object(
        adapter.connection, "request", side_effect=RequestError("Connection failed")
    ):
        with pytest.raises(ApiException):
            adapter.request("GET", "https://example.com")


def test_request_timeout_error():
    adapter = RESTClientObjectAdapter()

    with patch.object(
        adapter.connection, "request", side_effect=TimeoutException("Request timeout")
    ):
        with pytest.raises(ApiException):
            adapter.request("GET", "https://example.com")


def test_request_invalid_method():
    adapter = RESTClientObjectAdapter()

    with pytest.raises(AssertionError):
        adapter.request("INVALID", "https://example.com")


def test_request_body_and_post_params_conflict():
    adapter = RESTClientObjectAdapter()

    with pytest.raises(
        ValueError, match="body parameter cannot be used with post_params parameter"
    ):
        adapter.request(
            "POST",
            "https://example.com",
            body={"test": "data"},
            post_params={"field": "value"},
        )


def test_get_method():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter, "request", return_value=RESTResponse(mock_response)
    ) as mock_request:
        response = adapter.GET(
            "https://example.com", headers={"Accept": "application/json"}
        )

        mock_request.assert_called_once_with(
            "GET",
            "https://example.com",
            headers={"Accept": "application/json"},
            query_params=None,
            _preload_content=True,
            _request_timeout=None,
        )
        assert isinstance(response, RESTResponse)


def test_head_method():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b""
    mock_response.text = ""
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter, "request", return_value=RESTResponse(mock_response)
    ) as mock_request:
        response = adapter.HEAD("https://example.com")

        mock_request.assert_called_once_with(
            "HEAD",
            "https://example.com",
            headers=None,
            query_params=None,
            _preload_content=True,
            _request_timeout=None,
        )
        assert isinstance(response, RESTResponse)


def test_options_method():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"methods": ["GET", "POST"]}'
    mock_response.text = '{"methods": ["GET", "POST"]}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter, "request", return_value=RESTResponse(mock_response)
    ) as mock_request:
        response = adapter.OPTIONS("https://example.com", body={"test": "data"})

        mock_request.assert_called_once_with(
            "OPTIONS",
            "https://example.com",
            headers=None,
            query_params=None,
            post_params=None,
            body={"test": "data"},
            _preload_content=True,
            _request_timeout=None,
        )
        assert isinstance(response, RESTResponse)


def test_delete_method():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 204
    mock_response.reason_phrase = "No Content"
    mock_response.headers = {}
    mock_response.content = b""
    mock_response.text = ""
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter, "request", return_value=RESTResponse(mock_response)
    ) as mock_request:
        response = adapter.DELETE("https://example.com", body={"id": 123})

        mock_request.assert_called_once_with(
            "DELETE",
            "https://example.com",
            headers=None,
            query_params=None,
            body={"id": 123},
            _preload_content=True,
            _request_timeout=None,
        )
        assert isinstance(response, RESTResponse)


def test_post_method():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 201
    mock_response.reason_phrase = "Created"
    mock_response.headers = {}
    mock_response.content = b'{"id": 123}'
    mock_response.text = '{"id": 123}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter, "request", return_value=RESTResponse(mock_response)
    ) as mock_request:
        response = adapter.POST("https://example.com", body={"name": "test"})

        mock_request.assert_called_once_with(
            "POST",
            "https://example.com",
            headers=None,
            query_params=None,
            post_params=None,
            body={"name": "test"},
            _preload_content=True,
            _request_timeout=None,
        )
        assert isinstance(response, RESTResponse)


def test_put_method():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"updated": true}'
    mock_response.text = '{"updated": true}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter, "request", return_value=RESTResponse(mock_response)
    ) as mock_request:
        response = adapter.PUT("https://example.com", body={"name": "updated"})

        mock_request.assert_called_once_with(
            "PUT",
            "https://example.com",
            headers=None,
            query_params=None,
            post_params=None,
            body={"name": "updated"},
            _preload_content=True,
            _request_timeout=None,
        )
        assert isinstance(response, RESTResponse)


def test_patch_method():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"patched": true}'
    mock_response.text = '{"patched": true}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter, "request", return_value=RESTResponse(mock_response)
    ) as mock_request:
        response = adapter.PATCH("https://example.com", body={"field": "value"})

        mock_request.assert_called_once_with(
            "PATCH",
            "https://example.com",
            headers=None,
            query_params=None,
            post_params=None,
            body={"field": "value"},
            _preload_content=True,
            _request_timeout=None,
        )
        assert isinstance(response, RESTResponse)


def test_request_content_type_default():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter.connection, "request", return_value=mock_response
    ) as mock_request:
        adapter.request("POST", "https://example.com", body={"test": "data"})

        call_args = mock_request.call_args
        assert call_args[1]["headers"]["Content-Type"] == "application/json"


def test_request_content_type_override():
    adapter = RESTClientObjectAdapter()

    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.reason_phrase = "OK"
    mock_response.headers = {}
    mock_response.content = b'{"data": "test"}'
    mock_response.text = '{"data": "test"}'
    mock_response.url = "https://example.com"
    mock_response.http_version = "HTTP/1.1"

    with patch.object(
        adapter.connection, "request", return_value=mock_response
    ) as mock_request:
        adapter.request(
            "POST",
            "https://example.com",
            body="test",
            headers={"Content-Type": "text/plain"},
        )

        call_args = mock_request.call_args
        assert call_args[1]["headers"]["Content-Type"] == "text/plain"
