import base64
import warnings
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
    configuration = Configuration(server_api_url="https://user:password@play.orkes.io/api")
    basic_auth = "user:password"
    expected_host = f"https://{basic_auth}@play.orkes.io/api"
    assert configuration.host == expected_host
    token = "Basic " + base64.b64encode(bytes(basic_auth, "utf-8")).decode("utf-8")
    api_client = ApiClient(configuration)
    assert api_client.default_headers == {
        "Accept-Encoding": "gzip",
        "authorization": token,
    }


def test_base_url_with_api_path():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        configuration = Configuration(base_url="https://domain.com/api")
        assert len(w) == 1
        assert "base_url' been passed with '/api' path" in str(w[0].message)
        assert configuration.host == "https://domain.com/api"


def test_base_url_with_api_path_and_version():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        configuration = Configuration(base_url="https://domain.com/api/v1")
        assert len(w) == 1
        assert "base_url' been passed with '/api' path" in str(w[0].message)
        assert configuration.host == "https://domain.com/api/v1"


def test_base_url_with_api_subdomain_no_warning():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        configuration = Configuration(base_url="https://api.domain.com")
        assert len(w) == 0
        assert configuration.host == "https://api.domain.com/api"


def test_valid_base_url_no_warning():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        configuration = Configuration(base_url="https://domain.com")
        assert len(w) == 0
        assert configuration.host == "https://domain.com/api"


def test_base_url_with_port_no_warning():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        configuration = Configuration(base_url="https://domain.com:8080")
        assert len(w) == 0
        assert configuration.host == "https://domain.com:8080/api"


def test_base_url_with_api_subdomain_and_port_no_warning():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        configuration = Configuration(base_url="https://api.domain.com:8080")
        assert len(w) == 0
        assert configuration.host == "https://api.domain.com:8080/api"
def test_ssl_ca_cert_initialization():
    configuration = Configuration(
        base_url="https://internal.conductor.dev", ssl_ca_cert="/path/to/ca-cert.pem"
    )
    assert configuration.ssl_ca_cert == "/path/to/ca-cert.pem"
    assert configuration.ca_cert_data is None
    assert configuration.verify_ssl is True


def test_ca_cert_data_initialization_with_string():
    cert_data = "-----BEGIN CERTIFICATE-----\nMIIBIjANBgkqhkiG9w0B...\n-----END CERTIFICATE-----"
    configuration = Configuration(base_url="https://example.com", ca_cert_data=cert_data)
    assert configuration.ca_cert_data == cert_data
    assert configuration.ssl_ca_cert is None


def test_ca_cert_data_initialization_with_bytes():
    cert_data = b"-----BEGIN CERTIFICATE-----\nMIIBIjANBgkqhkiG9w0B...\n-----END CERTIFICATE-----"
    configuration = Configuration(base_url="https://internal.conductor.dev", ca_cert_data=cert_data)
    assert configuration.ca_cert_data == cert_data
    assert configuration.ssl_ca_cert is None


def test_ssl_options_combined():
    cert_data = "-----BEGIN CERTIFICATE-----\nMIIBIjANBgkqhkiG9w0B...\n-----END CERTIFICATE-----"
    configuration = Configuration(
        base_url="https://internal.conductor.dev",
        ssl_ca_cert="/path/to/ca-cert.pem",
        ca_cert_data=cert_data,
    )
    assert configuration.ssl_ca_cert == "/path/to/ca-cert.pem"
    assert configuration.ca_cert_data == cert_data


def test_ssl_defaults():
    configuration = Configuration(base_url="https://internal.conductor.dev")
    assert configuration.verify_ssl is True
    assert configuration.ssl_ca_cert is None
    assert configuration.ca_cert_data is None
    assert configuration.cert_file is None
    assert configuration.key_file is None
    assert configuration.assert_hostname is None


def test_cert_file_from_env(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_CERT_FILE", "/path/to/client-cert.pem")
    configuration = Configuration(base_url="https://internal.conductor.dev")
    assert configuration.cert_file == "/path/to/client-cert.pem"


def test_key_file_from_env(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_KEY_FILE", "/path/to/client-key.pem")
    configuration = Configuration(base_url="https://internal.conductor.dev")
    assert configuration.key_file == "/path/to/client-key.pem"


def test_verify_ssl_from_env_true(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_VERIFY_SSL", "true")
    configuration = Configuration(base_url="https://internal.conductor.dev")
    assert configuration.verify_ssl is True


def test_verify_ssl_from_env_false(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_VERIFY_SSL", "false")
    configuration = Configuration(base_url="https://internal.conductor.dev")
    assert configuration.verify_ssl is False


def test_ssl_ca_cert_data_from_env(monkeypatch):
    cert_data = "-----BEGIN CERTIFICATE-----\nMIIBIjANBgkqhkiG9w0B...\n-----END CERTIFICATE-----"
    monkeypatch.setenv("CONDUCTOR_SSL_CA_CERT_DATA", cert_data)
    configuration = Configuration(base_url="https://internal.conductor.dev")
    assert configuration.ca_cert_data == cert_data


def test_ssl_ca_cert_from_env(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_SSL_CA_CERT", "/path/to/ca-cert.pem")
    configuration = Configuration(base_url="https://internal.conductor.dev")
    assert configuration.ssl_ca_cert == "/path/to/ca-cert.pem"


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
        "User-Agent": "ConductorClient/1.0",
    }
    proxy_headers_json = json.dumps(complex_headers)
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", proxy_headers_json)
    configuration = Configuration()
    assert configuration.proxy_headers == complex_headers


def test_proxy_headers_json_with_special_chars(monkeypatch):
    special_headers = {
        "Authorization": "Bearer token with spaces and special chars!@#$%",
        "X-Header": "value with \"quotes\" and 'apostrophes'",
    }
    proxy_headers_json = json.dumps(special_headers)
    monkeypatch.setenv("CONDUCTOR_PROXY_HEADERS", proxy_headers_json)
    configuration = Configuration()
    assert configuration.proxy_headers == special_headers


def test_proxy_from_parameter():
    proxy_url = "http://proxy.company.com:8080"
    configuration = Configuration(proxy=proxy_url)
    assert configuration.proxy == proxy_url


def test_proxy_from_env(monkeypatch):
    proxy_url = "http://proxy.company.com:8080"
    monkeypatch.setenv("CONDUCTOR_PROXY", proxy_url)
    configuration = Configuration()
    assert configuration.proxy == proxy_url
