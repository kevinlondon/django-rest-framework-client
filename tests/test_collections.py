import pytest
import responses
from mock import patch

from drf_client.exceptions import APIException
from drf_client.resources import Resource, Collection
from drf_client import settings
from tests.helpers import mock_response
from tests.fixtures import authenticate


class ExampleCollection(Collection):
    collection_name = "foo"
    resource = "Resource"


@pytest.fixture
def collection():
    return ExampleCollection()


@pytest.fixture
def token():
    return '0acfe275e22451ad5fd294c798186b592c099707'


class TestCollection:

    @responses.activate
    def test_parse_resource_errors_on_failed_request(self, collection):
        response = mock_response(ok=False)
        with pytest.raises(APIException) as e:
            collection._parse_resource(response)
        assert 'Unable to parse foo' in str(e)

    def test_parse_resource_errors_on_missing_asset_info(self, collection):
        response = mock_response(ok=True, json_value={'results': {}})
        with pytest.raises(APIException) as e:
            collection._parse_resource(response)
        assert 'Unable to find the foo data' in str(e)

    def test_parse_resource_errors_on_no_assets_returned(self, collection):
        response = mock_response(
            ok=True, json_value={'results': {'foo': []}})
        with pytest.raises(APIException) as e:
            collection._parse_resource(response)
        assert 'No foo found' in str(e)

    def test_get_absolute_url_includes_collection_name(self, collection):
        collection.collection_name = "tests"
        abs_url = collection.get_absolute_url()
        expected_url = "{0}/tests".format(settings.API_URL)
        assert abs_url == expected_url

    @patch.object(Collection, "post")
    def test_create_calls_post(self, post_mock, collection):
        data = {"hi": "ok"}
        collection.create_resource(data)
        post_mock.assert_called_once_with(data)

    @patch.object(Collection, "_parse_resources")
    @patch('requests.post')
    def test_post_uses_correct_ssl_setting(self, request_mock, parse_mock,
                                           collection, authenticate):
        for setting in (True, False):
            settings.SSL_VERIFY = setting
            collection.post({})
            (_, called_kwargs) = request_mock.call_args
            assert called_kwargs['verify'] == setting


def test_format_data_transforms_resources_into_primary_key_values(collection):
    data = {"resource": Resource(id=5)}
    collection.format_data(data)
    assert data['resource'] == 5


class TestGet:

    @patch.object(Collection, "_parse_resources")
    @patch("drf_client.resources.issue_request")
    def _get_arguments_to_request(self, collection, request_mock, parse_mock,
                                  **kwargs):
        """Return a tuple of (args, kwargs)."""
        collection.get(**kwargs)
        return request_mock.call_args

    def _get_params(self, collection, **kwargs):
        args, kwargs = self._get_arguments_to_request(collection, **kwargs)
        return kwargs['params']

    def test_get_calls_get_request(self, collection):
        args, kwargs = self._get_arguments_to_request(collection)
        assert "get" in args

    def test_get_sets_limit_param(self, collection):
        params = self._get_params(collection)
        assert params['limit'] == 25

    def test_get_sets_offset_param(self, collection):
        params = self._get_params(collection)
        assert params['offset'] == 0

    def test_get_sets_sort_to_none_by_default(self, collection):
        params = self._get_params(collection)
        assert not params['sort']

    def test_can_set_limit_to_something_else(self, collection):
        new_limit = 5
        params = self._get_params(collection, limit=new_limit)
        assert params['limit'] == new_limit

    def test_cannot_set_limit_higher_than_500(self, collection):
        params = self._get_params(collection, limit=9001)
        assert params['limit'] == settings.MAX_PAGINATION_LIMIT

    def test_cannot_set_limit_or_offset_below_0(self, collection):
        params = self._get_params(collection, limit=-5, offset=-5)
        assert params['limit'] == 0
        assert params['offset'] == 0

    def test_sort_defaults_to_ascending_if_not_specified(self, collection):
        sortfield = "filename"
        params = self._get_params(collection, sort=sortfield)
        assert params['sort'] == "+{}".format(sortfield)

    def test_can_provide_any_filter(self, collection):
        params = self._get_params(collection, foo="bar")
        assert params['foo'] == "bar"
