import base64
import warnings

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
