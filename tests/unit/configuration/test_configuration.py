import base64
import json

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api_client import ApiClient


def test_initialization_default(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    configuration = Configuration()
    assert configuration.host == "http://localhost:8080/api"


def test_initialization_with_base_url():
    configuration = Configuration(base_url="https://play.orkes.io")
    assert configuration.host == "https://play.orkes.io/api"


def test_initialization_with_server_api_url():
    configuration = Configuration(server_api_url="https://play.orkes.io/api")
    assert configuration.host == "https://play.orkes.io/api"


def test_initialization_with_basic_auth_server_api_url():
    configuration = Configuration(
        server_api_url="https://user:password@play.orkes.io/api"
    )
    basic_auth = "user:password"
    expected_host = f"https://{basic_auth}@play.orkes.io/api"
    assert configuration.host == expected_host
    token = "Basic " + base64.b64encode(bytes(basic_auth, "utf-8")).decode("utf-8")
    api_client = ApiClient(configuration)
    assert api_client.default_headers == {
        "Accept-Encoding": "gzip",
        "authorization": token,
    }


def test_proxy_headers_from_parameter():
    proxy_headers = {"Authorization": "Bearer token123", "X-Custom": "value"}
    configuration = Configuration(proxy_headers=proxy_headers)
    assert configuration.proxy_headers == proxy_headers


def test_proxy_headers_from_env_valid_json(monkeypatch):
    proxy_headers_json = '{"Authorization": "Bearer token123", "X-Custom": "value"}'
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", proxy_headers_json)
    configuration = Configuration()
    expected_headers = {"Authorization": "Bearer token123", "X-Custom": "value"}
    assert configuration.proxy_headers == expected_headers


def test_proxy_headers_from_env_invalid_json_fallback(monkeypatch):
    invalid_json = "invalid-json-string"
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", invalid_json)
    configuration = Configuration()
    expected_headers = {"Authorization": "invalid-json-string"}
    assert configuration.proxy_headers == expected_headers


def test_proxy_headers_from_env_none_value_fallback(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", "None")
    configuration = Configuration()
    expected_headers = {"Authorization": "None"}
    assert configuration.proxy_headers == expected_headers


def test_proxy_headers_from_env_empty_string_no_processing(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", "")
    configuration = Configuration()
    assert configuration.proxy_headers is None


def test_proxy_headers_from_env_malformed_json_fallback(monkeypatch):
    malformed_json = '{"Authorization": "Bearer token", "X-Custom":}'
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", malformed_json)
    configuration = Configuration()
    expected_headers = {"Authorization": malformed_json}
    assert configuration.proxy_headers == expected_headers


def test_proxy_headers_no_env_var():
    configuration = Configuration()
    assert configuration.proxy_headers is None


def test_proxy_headers_parameter_overrides_env(monkeypatch):
    proxy_headers_param = {"Authorization": "Bearer param-token"}
    proxy_headers_env = '{"Authorization": "Bearer env-token"}'
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", proxy_headers_env)
    configuration = Configuration(proxy_headers=proxy_headers_param)
    assert configuration.proxy_headers == proxy_headers_param


def test_proxy_headers_complex_json(monkeypatch):
    complex_headers = {
        "Authorization": "Bearer token123",
        "X-API-Key": "api-key-456",
        "X-Custom-Header": "custom-value",
        "User-Agent": "ConductorClient/1.0"
    }
    proxy_headers_json = json.dumps(complex_headers)
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", proxy_headers_json)
    configuration = Configuration()
    assert configuration.proxy_headers == complex_headers


def test_proxy_headers_json_with_special_chars(monkeypatch):
    special_headers = {
        "Authorization": "Bearer token with spaces and special chars!@#$%",
        "X-Header": "value with \"quotes\" and 'apostrophes'"
    }
    proxy_headers_json = json.dumps(special_headers)
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", proxy_headers_json)
    configuration = Configuration()
    assert configuration.proxy_headers == special_headers
