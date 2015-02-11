"""
drf_client SDK: Auth

Concrete implementation of the AuthManager.
"""
from drf_client import settings


def set_token(token):
    """Configure the settings to include the API token.

    Raises:
        TypeError: If a non-string token is provided.
    """
    if not isinstance(token, basestring):
        raise TypeError("Incorrect format for API token.")

    settings.API_TOKEN = token


def get_headers():
    """Returns a formatted authentication header.

    Raises:
        ValueError: if no value has been set for the token.
    """
    token = settings.API_TOKEN
    if not token:
        raise ValueError("No API token value set.")

    return {'Authorization': 'Bearer {0}'.format(token),
            'Content-Type': "application/json"}
