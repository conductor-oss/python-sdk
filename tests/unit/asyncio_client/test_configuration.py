import os
import logging
from unittest.mock import patch, MagicMock
import pytest

from conductor.asyncio_client.configuration.configuration import Configuration


def test_initialization_default():
    config = Configuration()
    assert config.server_url is not None
    assert config.polling_interval == 100
    assert config.domain == "default_domain"
    assert config.polling_interval_seconds == 0
    assert config.debug is False


def test_initialization_with_parameters():
    config = Configuration(
        server_url="https://test.com/api",
        auth_key="test_key",
        auth_secret="test_secret",
        debug=True,
        polling_interval=200,
        domain="test_domain",
        polling_interval_seconds=5,
    )
    assert config.server_url == "https://test.com/api"
    assert config.auth_key == "test_key"
    assert config.auth_secret == "test_secret"
    assert config.debug is True
    assert config.polling_interval == 200
    assert config.domain == "test_domain"
    assert config.polling_interval_seconds == 5


def test_initialization_with_env_vars(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_SERVER_URL", "https://env.com/api")
    monkeypatch.setenv("CONDUCTOR_AUTH_KEY", "env_key")
    monkeypatch.setenv("CONDUCTOR_AUTH_SECRET", "env_secret")
    monkeypatch.setenv("CONDUCTOR_WORKER_POLL_INTERVAL", "300")
    monkeypatch.setenv("CONDUCTOR_WORKER_DOMAIN", "env_domain")
    monkeypatch.setenv("CONDUCTOR_WORKER_POLL_INTERVAL_SECONDS", "10")

    config = Configuration()
    assert config.server_url == "https://env.com/api"
    assert config.auth_key == "env_key"
    assert config.auth_secret == "env_secret"
    assert config.polling_interval == 300
    assert config.domain == "env_domain"
    assert config.polling_interval_seconds == 10

def test_initialization_env_vars_override_params(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_SERVER_URL", "https://env.com/api")
    monkeypatch.setenv("CONDUCTOR_AUTH_KEY", "env_key")

    config = Configuration(server_url="https://param.com/api", auth_key="param_key")
    assert config.server_url == "https://param.com/api"
    assert config.auth_key == "param_key"


def test_initialization_empty_server_url():
    config = Configuration(server_url="")
    assert config.server_url == "http://localhost:8080/api"


def test_initialization_none_server_url():
    config = Configuration(server_url=None)
    assert config.server_url is not None


def test_ui_host_default():
    config = Configuration(server_url="https://test.com/api")
    assert config.ui_host == "https://test.com"


def test_ui_host_env_var(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_UI_SERVER_URL", "https://ui.com")
    config = Configuration()
    assert config.ui_host == "https://ui.com"


def test_get_env_int_valid():
    config = Configuration()
    with patch.dict(os.environ, {"TEST_INT": "42"}):
        result = config._get_env_int("TEST_INT", 10)
        assert result == 42


def test_get_env_int_invalid():
    config = Configuration()
    with patch.dict(os.environ, {"TEST_INT": "invalid"}):
        result = config._get_env_int("TEST_INT", 10)
        assert result == 10


def test_get_env_int_missing():
    config = Configuration()
    with patch.dict(os.environ, {}, clear=True):
        result = config._get_env_int("TEST_INT", 10)
        assert result == 10


def test_get_env_float_valid():
    config = Configuration()
    with patch.dict(os.environ, {"TEST_FLOAT": "3.14"}):
        result = config._get_env_float("TEST_FLOAT", 1.0)
        assert result == 3.14


def test_get_env_float_invalid():
    config = Configuration()
    with patch.dict(os.environ, {"TEST_FLOAT": "invalid"}):
        result = config._get_env_float("TEST_FLOAT", 1.0)
        assert result == 1.0


def test_get_worker_property_value_task_specific(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_MYTASK_POLLING_INTERVAL", "500")
    config = Configuration()
    result = config.get_worker_property_value("polling_interval", "mytask")
    assert result == 500.0


def test_get_worker_property_value_global(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_POLLING_INTERVAL", "600")
    config = Configuration()
    result = config.get_worker_property_value("polling_interval", "mytask")
    assert result == 600.0


def test_get_worker_property_value_default():
    config = Configuration()
    result = config.get_worker_property_value("polling_interval", "mytask")
    assert result == 100


def test_get_worker_property_value_domain():
    config = Configuration()
    result = config.get_worker_property_value("domain", "mytask")
    assert result == "default_domain"


def test_get_worker_property_value_poll_interval_seconds():
    config = Configuration()
    result = config.get_worker_property_value("poll_interval_seconds", "mytask")
    assert result == 0

def test_convert_property_value_polling_interval():
    config = Configuration()
    result = config._convert_property_value("polling_interval", "250")
    assert result == 250.0


def test_convert_property_value_polling_interval_invalid():
    config = Configuration()
    result = config._convert_property_value("polling_interval", "invalid")
    assert result == 100


def test_convert_property_value_polling_interval_seconds():
    config = Configuration()
    result = config._convert_property_value("polling_interval_seconds", "5")
    assert result == 5.0


def test_convert_property_value_polling_interval_seconds_invalid():
    config = Configuration()
    result = config._convert_property_value("polling_interval_seconds", "invalid")
    assert result == 0


def test_convert_property_value_string():
    config = Configuration()
    result = config._convert_property_value("domain", "test_domain")
    assert result == "test_domain"


def test_set_worker_property():
    config = Configuration()
    config.set_worker_property("mytask", "polling_interval", 300)
    assert config._worker_properties["mytask"]["polling_interval"] == 300


def test_set_worker_property_multiple():
    config = Configuration()
    config.set_worker_property("mytask", "polling_interval", 300)
    config.set_worker_property("mytask", "domain", "test_domain")
    assert config._worker_properties["mytask"]["polling_interval"] == 300
    assert config._worker_properties["mytask"]["domain"] == "test_domain"


def test_get_worker_property():
    config = Configuration()
    config.set_worker_property("mytask", "polling_interval", 300)
    result = config.get_worker_property("mytask", "polling_interval")
    assert result == 300


def test_get_worker_property_not_found():
    config = Configuration()
    result = config.get_worker_property("mytask", "polling_interval")
    assert result is None


def test_get_polling_interval_with_task_type(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_MYTASK_POLLING_INTERVAL", "400")
    config = Configuration()
    result = config.get_polling_interval("mytask")
    assert result == 400.0


def test_get_polling_interval_default():
    config = Configuration()
    result = config.get_polling_interval("mytask")
    assert result == 100.0


def test_get_domain_with_task_type(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_MYTASK_DOMAIN", "task_domain")
    config = Configuration()
    result = config.get_domain("mytask")
    assert result == "task_domain"


def test_get_domain_default():
    config = Configuration()
    result = config.get_domain("mytask")
    assert result == "default_domain"


def test_get_poll_interval_with_task_type(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_WORKER_MYTASK_POLLING_INTERVAL", "500")
    config = Configuration()
    result = config.get_poll_interval("mytask")
    assert result == 500


def test_get_poll_interval_default():
    config = Configuration()
    result = config.get_poll_interval("mytask")
    assert result == 100


def test_get_poll_interval_seconds():
    config = Configuration()
    result = config.get_poll_interval_seconds()
    assert result == 0


def test_host_property():
    config = Configuration(server_url="https://test.com/api")
    assert config.host == "https://test.com/api"


def test_host_setter():
    config = Configuration()
    config.host = "https://new.com/api"
    assert config.host == "https://new.com/api"


def test_debug_property():
    config = Configuration(debug=True)
    assert config.debug is True


def test_debug_setter():
    config = Configuration()
    config.debug = True
    assert config.debug is True


def test_api_key_property():
    config = Configuration()
    config.api_key = {"test": "value"}
    assert config.api_key == {"test": "value"}


def test_api_key_prefix_property():
    config = Configuration()
    config.api_key_prefix = {"test": "prefix"}
    assert config.api_key_prefix == {"test": "prefix"}


def test_username_property():
    config = Configuration()
    config.username = "testuser"
    assert config.username == "testuser"


def test_password_property():
    config = Configuration()
    config.password = "testpass"
    assert config.password == "testpass"


def test_access_token_property():
    config = Configuration()
    config.access_token = "testtoken"
    assert config.access_token == "testtoken"


def test_verify_ssl_property():
    config = Configuration()
    config.verify_ssl = False
    assert config.verify_ssl is False


def test_ssl_ca_cert_property():
    config = Configuration()
    config.ssl_ca_cert = "/path/to/cert"
    assert config.ssl_ca_cert == "/path/to/cert"


def test_retries_property():
    config = Configuration()
    config.retries = 5
    assert config.retries == 5


def test_logger_format_property():
    config = Configuration()
    config.logger_format = "%(message)s"
    assert config.logger_format == "%(message)s"


def test_log_level_property():
    config = Configuration(debug=True)
    assert config.log_level == logging.DEBUG


def test_apply_logging_config():
    config = Configuration()
    config.apply_logging_config()
    assert config.is_logger_config_applied is True


def test_apply_logging_config_custom():
    config = Configuration()
    config.apply_logging_config(log_format="%(message)s", level=logging.ERROR)
    assert config.is_logger_config_applied is True


def test_apply_logging_config_already_applied():
    config = Configuration()
    config.apply_logging_config()
    config.apply_logging_config()
    assert config.is_logger_config_applied is True


def test_get_logging_formatted_name():
    result = Configuration.get_logging_formatted_name("test_logger")
    assert result.startswith("[pid:")
    assert result.endswith("] test_logger")


def test_ui_host_property():
    config = Configuration(server_url="https://test.com/api")
    assert config.ui_host == "https://test.com"


def test_getattr_delegation():
    config = Configuration()
    mock_config = MagicMock()
    config._http_config = mock_config
    mock_config.test_attr = "test_value"

    result = config.test_attr
    assert result == "test_value"


def test_getattr_no_http_config():
    config = Configuration()
    config._http_config = None

    with pytest.raises(AttributeError):
        _ = config.nonexistent_attr


def test_worker_properties_dict_initialization():
    config = Configuration()
    assert isinstance(config._worker_properties, dict)
    assert len(config._worker_properties) == 0


def test_get_worker_property_value_unknown_property():
    config = Configuration()
    result = config.get_worker_property_value("unknown_property", "mytask")
    assert result is None


def test_get_poll_interval_with_task_type_none_value():
    config = Configuration()
    with patch.dict(os.environ, {"CONDUCTOR_WORKER_MYTASK_POLLING_INTERVAL": "invalid"}):
        result = config.get_poll_interval("mytask")
        assert result == 100


def test_host_property_no_http_config():
    config = Configuration()
    config._http_config = None
    config._host = "test_host"
    assert config.host == "test_host"


def test_debug_setter_false():
    config = Configuration(debug=True)
    config.debug = False
    assert config.debug is False


def test_proxy_initialization_from_parameter():
    config = Configuration(proxy="http://proxy.example.com:8080")
    assert config.proxy == "http://proxy.example.com:8080"
    assert config._http_config.proxy == "http://proxy.example.com:8080"


def test_proxy_initialization_from_env_var(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_PROXY", "http://env-proxy.example.com:3128")
    config = Configuration()
    assert config.proxy == "http://env-proxy.example.com:3128"
    assert config._http_config.proxy == "http://env-proxy.example.com:3128"


def test_proxy_parameter_overrides_env_var(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_PROXY", "http://env-proxy.example.com:3128")
    config = Configuration(proxy="http://param-proxy.example.com:8080")
    assert config.proxy == "http://param-proxy.example.com:8080"
    assert config._http_config.proxy == "http://param-proxy.example.com:8080"


def test_proxy_headers_initialization_from_parameter():
    headers = {"Authorization": "Bearer token123", "X-Custom": "value"}
    config = Configuration(proxy_headers=headers)
    assert config.proxy_headers == headers
    assert config._http_config.proxy_headers == headers


def test_proxy_headers_initialization_from_env_var_json(monkeypatch):
    headers_json = '{"Authorization": "Bearer token123", "X-Custom": "value"}'
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", headers_json)
    config = Configuration()
    expected_headers = {"Authorization": "Bearer token123", "X-Custom": "value"}
    assert config.proxy_headers == expected_headers
    assert config._http_config.proxy_headers == expected_headers


def test_proxy_headers_initialization_from_env_var_single_header(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", "Bearer single-token")
    config = Configuration()
    expected_headers = {"Authorization": "Bearer single-token"}
    assert config.proxy_headers == expected_headers
    assert config._http_config.proxy_headers == expected_headers


def test_proxy_headers_parameter_overrides_env_var(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", '{"Authorization": "env-token"}')
    param_headers = {"Authorization": "param-token", "X-Custom": "value"}
    config = Configuration(proxy_headers=param_headers)
    assert config.proxy_headers == param_headers
    assert config._http_config.proxy_headers == param_headers


def test_proxy_headers_invalid_json_falls_back_to_single_header(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", "invalid-json-string")
    config = Configuration()
    expected_headers = {"Authorization": "invalid-json-string"}
    assert config.proxy_headers == expected_headers
    assert config._http_config.proxy_headers == expected_headers


def test_proxy_headers_none_when_no_env_var():
    config = Configuration()
    assert config.proxy_headers is None
    assert config._http_config.proxy_headers is None


def test_proxy_none_when_no_env_var():
    config = Configuration()
    assert config.proxy is None
    assert config._http_config.proxy is None


def test_proxy_and_headers_together():
    headers = {"Authorization": "Bearer token123"}
    config = Configuration(
        proxy="http://proxy.example.com:8080",
        proxy_headers=headers
    )
    assert config.proxy == "http://proxy.example.com:8080"
    assert config.proxy_headers == headers
    assert config._http_config.proxy == "http://proxy.example.com:8080"
    assert config._http_config.proxy_headers == headers


def test_proxy_headers_empty_json_parses_correctly(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", "{}")
    config = Configuration()
    expected_headers = {}
    assert config.proxy_headers == expected_headers
    # Empty dict is falsy, so it's not set on HTTP config
    assert config._http_config.proxy_headers is None


def test_proxy_headers_env_var_with_none_value(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", "None")
    config = Configuration()
    expected_headers = {"Authorization": "None"}
    assert config.proxy_headers == expected_headers
    assert config._http_config.proxy_headers == expected_headers


def test_proxy_https_url():
    config = Configuration(proxy="https://secure-proxy.example.com:8443")
    assert config.proxy == "https://secure-proxy.example.com:8443"
    assert config._http_config.proxy == "https://secure-proxy.example.com:8443"


def test_proxy_socks_url():
    config = Configuration(proxy="socks5://socks-proxy.example.com:1080")
    assert config.proxy == "socks5://socks-proxy.example.com:1080"
    assert config._http_config.proxy == "socks5://socks-proxy.example.com:1080"


def test_proxy_headers_multiple_headers():
    headers = {
        "Authorization": "Bearer token123",
        "X-API-Key": "api-key-456",
        "User-Agent": "CustomAgent/1.0"
    }
    config = Configuration(proxy_headers=headers)
    assert config.proxy_headers == headers
    assert config._http_config.proxy_headers == headers


def test_proxy_headers_with_special_characters():
    headers = {
        "Authorization": "Bearer token with spaces",
        "X-Custom-Header": "value-with-special-chars!@#$%"
    }
    config = Configuration(proxy_headers=headers)
    assert config.proxy_headers == headers
    assert config._http_config.proxy_headers == headers

def test_get_poll_interval_with_task_type_none():
    config = Configuration()
    result = config.get_poll_interval("mytask")
    assert result == 100


def test_get_poll_interval_task_type_provided_but_value_none():
    config = Configuration()
    with patch.dict(os.environ, {"CONDUCTOR_WORKER_MYTASK_POLLING_INTERVAL": ""}):
        result = config.get_poll_interval("mytask")
        assert result == 100
