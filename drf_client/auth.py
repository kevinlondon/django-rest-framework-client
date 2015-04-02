"""
drf_client SDK: Auth

Concrete implementation of the AuthManager.
"""

from base64 import b64encode


def _set_authentication(authentication):
    from drf_client import settings
    settings.AUTHENTICATION = authentication


def set_token(token):
    _set_authentication(TokenAuthentication(token=token))


def log_in(username, password):
    _set_authentication(BasicAuthentication(username, password))


class AuthenticationBase(object):
    """Abstract base class."""

    def get_header(self):
        try:
            auth = "{0} {1}".format(self.prefix, self.authentication)
        except AttributeError:
            return {}

        return {"Authorization": auth}


class BasicAuthentication(AuthenticationBase):

    prefix = "Basic"

    def __init__(self, username, password):
        self.authenticate(username, password)

    def authenticate(self, username, password):
        if not username:
            raise ValueError("No user provided.")
        elif not password:
            raise ValueError("No password provided.")

        userstr = "{0}:{1}".format(username, password).encode("latin1")
        self.authentication = b64encode(userstr.strip())


class TokenAuthentication(AuthenticationBase):

    prefix = "Token"

    def __init__(self, token):
        self.authenticate(token)

    def authenticate(self, value):
        """Configure the settings to include the API token.

        Raises:
            TypeError: If a non-string token is provided.
        """
        if not isinstance(value, basestring):
            raise TypeError("Incorrect format for API token.")

        self.authentication = value
