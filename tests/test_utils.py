import mock
from mock import patch
import pytest
import responses

from drf_client import utils, settings
from drf_client.resources import Resource
from drf_client.exceptions import APIException
from tests.fixtures import authenticate
from tests.helpers import mock_response


def test_converting_objs_to_ids_works_with_multiple():
    user = mock.Mock(id=1)
    ids = utils.convert_to_ids(user)
    assert ids == [1, ]


def test_converting_objs_to_ids_works_with_single():
    users = [mock.Mock(id=x) for x in xrange(3)]
    ids = utils.convert_to_ids(users)
    assert ids == [user.id for user in users]


class TestParseResource:

    @responses.activate
    def test_parse_resource_errors_on_failed_request(self):
        response = mock_response(ok=False)
        with pytest.raises(APIException) as e:
            utils.parse_resources(cls=None, response=response)
        assert 'Unsuccessful response' in str(e)

    def test_parse_resource_errors_on_missing_asset_info(self):
        response = mock_response(ok=True, json_value={'results': {}})
        with pytest.raises(APIException) as e:
            utils.parse_resources(cls=None, response=response)
        assert 'Unable to find' in str(e)

    def test_parse_resource_errors_on_no_assets_returned(self):
        response = mock_response(ok=True, json_value={'results': {'foo': []}})
        with pytest.raises(APIException) as e:
            utils.parse_resources(cls=None, response=response, many=True)
        assert 'Response did not return a list' in str(e)

    def test_parse_resources_works_fine_when_many_is_True_and_list(self):
        entry = {"foo": []}
        response = mock_response(ok=True, json_value={'results': [entry, ]})
        resources = utils.parse_resources(cls=Resource, response=response, many=True)
        assert len(resources) == 1
        assert resources[0].raw_data == entry

    def test_parse_resource_does_not_dig_into_response_when_many_is_false(self):
        data = {"foo": []}
        response = mock_response(ok=True, json_value=data)
        resource = utils.parse_resources(cls=Resource, response=response, many=False)
        assert resource.raw_data == data

