import mock
from mock import patch
import pytest

from drf_client import utils, resources
from .fixtures import authenticate


@pytest.fixture
def collection():
    return resources.Collection()


@patch("requests.get")
def test_issue_request_appends_ids_to_url(get_mock, collection, authenticate):
    utils.issue_request("get", instance=collection, ids=[10, 2])
    called_url = get_mock.call_args[0][0]
    expected_url = "{0}/10,2".format(collection.get_absolute_url())
    assert called_url == expected_url


@patch("requests.get")
def test_issue_request_doesnt_append_if_no_ids(get_mock, collection, authenticate):
    utils.issue_request("get", instance=collection, ids=None)
    called_url = get_mock.call_args[0][0]
    assert called_url == collection.get_absolute_url()


def test_converting_objs_to_ids_works_with_multiple():
    user = mock.Mock(id=1)
    ids = utils.convert_to_ids(user)
    assert ids == [1, ]


@patch("requests.get")
def test_params_are_passed_to_request(get_mock, collection):
    params = {"foo": True}
    utils.issue_request("get", instance=collection, params=params)
    args, kwargs = get_mock.call_args
    assert kwargs["params"] == params


def test_converting_objs_to_ids_works_with_single():
    users = [mock.Mock(id=x) for x in xrange(3)]
    ids = utils.convert_to_ids(users)
    assert ids == [user.id for user in users]
