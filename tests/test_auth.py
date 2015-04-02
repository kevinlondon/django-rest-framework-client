"""
drf_client SDK: Auth Tests

Tests for the drf_client AuthManager
"""

from base64 import b64encode
import pytest
from collections import namedtuple

from drf_client import auth, settings
from drf_client.auth import (
    TokenAuthentication, AuthenticationBase, BasicAuthentication
)


@pytest.fixture
def reset_auth():
    settings.AUTHENTICATION = AuthenticationBase()


class TestBasicAuthentication:

    @pytest.fixture
    def user(self):
        User = namedtuple("User", ["username", "password"])
        return User("user", "pass")

    def test_log_in_sets_basic_authentication_class(self, user, reset_auth):
        assert isinstance(settings.AUTHENTICATION, AuthenticationBase)
        auth.log_in(username=user.username, password=user.password)
        assert isinstance(settings.AUTHENTICATION, BasicAuthentication)

    def test_get_header_returns_base_64_encoded_string(self, user, reset_auth):
        auth.log_in(*user)
        auth_header = settings.AUTHENTICATION.get_header()
        user_string = "{0}:{1}".format(user.username, user.password)
        base64_login = b64encode(user_string.encode('latin1')).strip()
        expected_header = {"Authorization": "Basic {0}".format(base64_login)}
        assert auth_header == expected_header


class TestTokenAuthentication:

    @pytest.fixture
    def token(self):
        return '1234567890123456789012345678901234567890'

    def test_register_token_errors_on_non_string(self):
        tokens = [123, True, ('Let me', 'in')]
        for token in tokens:
            with pytest.raises(TypeError):
                auth.set_token(token)

    def test_register_token_registers_as_expected(self, token, reset_auth):
        assert isinstance(settings.AUTHENTICATION, AuthenticationBase)
        auth.set_token(token)
        assert isinstance(settings.AUTHENTICATION, TokenAuthentication)
        assert settings.AUTHENTICATION.authentication == token

    def test_get_registered_token_errors_if_nothing_registered(self, reset_auth):
        with pytest.raises(ValueError):
            settings.AUTHENTICATION.get_header()

    def test_get_headers_returns_correct_structure(self, token):
        auth.set_token(token)
        expected_headers = {'Authorization': 'Token {0}'.format(token)}
        headers = settings.AUTHENTICATION.get_header()
        for key, value in expected_headers.iteritems():
            assert headers[key] == value
