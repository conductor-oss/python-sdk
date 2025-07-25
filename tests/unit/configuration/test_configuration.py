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
    configuration = Configuration(server_api_url="https://user:password@play.orkes.io/api")
    basic_auth = "user:password"
    expected_host = f"https://{basic_auth}@play.orkes.io/api"
    assert configuration.host == expected_host
    token = "Basic " + base64.b64encode(bytes(basic_auth, "utf-8")).decode("utf-8")
    api_client = ApiClient(configuration)
    assert api_client.default_headers == {"Accept-Encoding": "gzip", "authorization": token}
