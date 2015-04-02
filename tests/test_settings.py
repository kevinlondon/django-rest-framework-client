import os
from mock import patch
import pytest

import drf_client
from drf_client import settings


@pytest.fixture
def config_path():
    return os.path.join(os.path.dirname(__file__), "config.yaml")


@pytest.fixture
def reset():
    reload(settings)


@patch.object(drf_client, "authenticate")
class TestConfigure:

    def test_updates_host(self, auth, config_path, reset):
        assert settings.HOST == "0.0.0.0:8000"
        drf_client.configure(config_path)
        assert settings.HOST == "localhost:8000"

    def test_auth_unchanged(self, auth, config_path, reset):
        base_auth = settings.AUTHENTICATION
        drf_client.configure(config_path)
        assert settings.AUTHENTICATION == base_auth

    def test_api_url_changes_after_load(self, auth, config_path, reset):
        assert settings.API_URL == "http://0.0.0.0:8000"
        drf_client.configure(config_path)
        assert settings.API_URL == "http://localhost:8000"


class TestLogin:

    def test_configure_sets_auth_if_user_and_pword(self, config_path, reset):
        with patch.object(drf_client, "authenticate") as auth_mock:
            drf_client.configure(config_path, username="foo", password="bar")
            auth_mock.assert_called_with("foo", "bar", None)

    @patch.object(drf_client.auth, "log_in")
    def test_authenticate_with_username_and_pass_calls_login(self, log_in):
        drf_client.authenticate(username="foo", password="bar", token=None)
        log_in.assert_called_with(username="foo", password="bar")

    @patch.object(drf_client.auth, "set_token")
    def test_authenticate_calls_set_token_if_token(self, set_token):
        drf_client.authenticate(username=None, password=None, token="blah")
        set_token.assert_called_with(token="blah")
