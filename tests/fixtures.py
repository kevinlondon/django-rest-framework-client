import pytest
from drf_client import auth


@pytest.fixture
def authenticate():
    auth.set_token("abcdef")
