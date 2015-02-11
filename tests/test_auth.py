"""
drf_client SDK: Auth Tests

Tests for the drf_client AuthManager
"""

import pytest

from drf_client import auth, settings


class TestAuth:

    @pytest.fixture
    def token(self):
        return '1234567890123456789012345678901234567890'

    @pytest.fixture
    def clean_auth(self):
        settings.API_TOKEN = None

    def test_register_token_errors_on_non_string(self):
        tokens = [123, True, ('Let me', 'in')]
        for token in tokens:
            with pytest.raises(TypeError):
                auth.set_token(token)

    def test_register_token_registers_as_expected(self, token, clean_auth):
        assert settings.API_TOKEN is None
        auth.set_token(token)
        assert settings.API_TOKEN == token

    def test_get_registered_token_errors_if_nothing_registered(self, clean_auth):
        with pytest.raises(ValueError):
            auth.get_headers()

    def test_get_headers_returns_correct_structure(self, token):
        auth.set_token(token)
        expected_headers = {'Content-Type': 'application/json',
                            'Authorization': 'Bearer %s' % token}
        headers = auth.get_headers()
        for key, value in expected_headers.iteritems():
            assert headers[key] == value
