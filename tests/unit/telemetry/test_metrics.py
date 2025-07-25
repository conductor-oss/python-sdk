import logging
import pytest
from conductor.client.configuration.settings.metrics_settings import MetricsSettings


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


def test_default_initialization():
    metrics_settings = MetricsSettings()
    assert metrics_settings.file_name == "metrics.log"
    assert metrics_settings.update_interval == 0.1


def test_default_initialization_with_parameters():
    expected_directory = "/a/b"
    expected_file_name = "some_name.txt"
    expected_update_interval = 0.5
    metrics_settings = MetricsSettings(
        directory=expected_directory,
        file_name=expected_file_name,
        update_interval=expected_update_interval,
    )
    assert metrics_settings.file_name == expected_file_name
    assert metrics_settings.update_interval == expected_update_interval
