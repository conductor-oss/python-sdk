import pytest

from conductor.asyncio_client.configuration import Configuration


def test_initialization_default(monkeypatch):
    monkeypatch.setenv("CONDUCTOR_SERVER_URL", "http://localhost:8080/api")
    configuration = Configuration()
    assert configuration.host == "http://localhost:8080/api"


def test_initialization_with_base_url():
    configuration = Configuration(server_url="https://play.orkes.io/api")
    assert configuration.host == "https://play.orkes.io/api"


def test_missed_http_config():
    configuration = Configuration()
    configuration._http_config = None
    with pytest.raises(AttributeError) as ctx:
        _ = configuration.api_key
        assert (
            f"'{Configuration.__class__.__name__}' object has no attribute 'api_key'"
            in ctx.value
        )
