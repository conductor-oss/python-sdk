import base64

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


def test_ssl_ca_cert_initialization():
    configuration = Configuration(
        base_url="https://internal.conductor.dev",
        ssl_ca_cert="/path/to/ca-cert.pem"
    )
    assert configuration.ssl_ca_cert == "/path/to/ca-cert.pem"
    assert configuration.ca_cert_data is None
    assert configuration.verify_ssl is True


def test_ca_cert_data_initialization_with_string():
    cert_data = "-----BEGIN CERTIFICATE-----\nMIIBIjANBgkqhkiG9w0B...\n-----END CERTIFICATE-----"
    configuration = Configuration(
        base_url="https://example.com",
        ca_cert_data=cert_data
    )
    assert configuration.ca_cert_data == cert_data
    assert configuration.ssl_ca_cert is None


def test_ca_cert_data_initialization_with_bytes():
    cert_data = b"-----BEGIN CERTIFICATE-----\nMIIBIjANBgkqhkiG9w0B...\n-----END CERTIFICATE-----"
    configuration = Configuration(
        base_url="https://internal.conductor.dev",
        ca_cert_data=cert_data
    )
    assert configuration.ca_cert_data == cert_data
    assert configuration.ssl_ca_cert is None


def test_ssl_options_combined():
    cert_data = "-----BEGIN CERTIFICATE-----\nMIIBIjANBgkqhkiG9w0B...\n-----END CERTIFICATE-----"
    configuration = Configuration(
        base_url="https://internal.conductor.dev",
        ssl_ca_cert="/path/to/ca-cert.pem",
        ca_cert_data=cert_data
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
