import os
import pytest

import drf_client
from drf_client import settings


@pytest.fixture
def config_path():
    return os.path.join(os.path.dirname(__file__), "config.yaml")


@pytest.fixture
def reset():
    reload(settings)


class TestConfigure:

    def test_updates_host(self, config_path, reset):
        assert settings.HOST == "0.0.0.0:8000"
        drf_client.configure(config_path)
        assert settings.HOST == "localhost:8000"

    def test_authentication_unchanged_when_not_in_cfg(self, config_path, reset):
        base_auth = settings.AUTHENTICATION
        drf_client.configure(config_path)
        assert settings.AUTHENTICATION == base_auth

    def test_api_url_changes_after_load(self, config_path, reset):
        assert settings.API_URL == "http://0.0.0.0:8000"
        drf_client.configure(config_path)
        assert settings.API_URL == "http://localhost:8000"
