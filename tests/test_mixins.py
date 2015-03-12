import pytest
import responses
from mock import patch, Mock

from drf_client import utils, mixins, settings
from drf_client.exceptions import APIException
from drf_client.resources import Resource
from drf_client.mixins import GetMixin, CreateMixin


@pytest.fixture
def resource():
    return Resource()


class TestGet:

    @patch.object(mixins, "parse_resources")
    @patch.object(mixins, "request")
    def _get_arguments_to_request(self, request_mock, parse_mock, **kwargs):
        """Return a tuple of (args, kwargs)."""
        Resource.get(**kwargs)
        assert request_mock.called
        return request_mock.call_args

    def _get_params(self, **kwargs):
        args, kwargs = self._get_arguments_to_request(**kwargs)
        return kwargs['params']

    def test_get_calls_get_request(self):
        args, kwargs = self._get_arguments_to_request()
        assert "get" in args

    def test_get_sets_limit_param(self):
        params = self._get_params()
        assert params['limit'] == 25

    def test_get_sets_offset_param(self):
        params = self._get_params()
        assert params['offset'] == 0

    def test_can_set_limit_to_something_else(self):
        new_limit = 5
        params = self._get_params(limit=new_limit)
        assert params['limit'] == new_limit

    def test_cannot_set_limit_higher_than_500(self):
        params = self._get_params(limit=settings.MAX_PAGINATION_LIMIT+10)
        assert params['limit'] == settings.MAX_PAGINATION_LIMIT

    def test_cannot_set_limit_or_offset_below_0(self):
        params = self._get_params(limit=-5, offset=-5)
        assert params['limit'] == 0
        assert params['offset'] == 0

    def test_can_provide_any_filter(self):
        params = self._get_params(foo="bar")
        assert params['foo'] == "bar"

    @patch.object(mixins, "parse_resources", return_value="foo")
    @patch.object(mixins, "request", return_value="baz")
    def test_get_calls_issue_request_and_parse(self, request_mock, parse_mock):
        GetMixin._route = Mock()
        GetMixin.get_collection_url = Mock()
        assert GetMixin.get() == "foo"
        assert request_mock.called
        parse_mock.assert_called_once_with(GetMixin, "baz")


class TestCreate:

    @patch("drf_client.mixins.request")
    @patch.object(Resource, "run_validation")
    def test_calls_validation_on_model(self, validation_mock, request_mock):
        data = {"foo": "bar"}
        try:
            instance = Resource.create(foo="bar")
        except APIException:
            # Still fine, ignore
            pass
        validation_mock.assert_called_with(data)

    @patch("drf_client.mixins.request")
    @patch.object(Resource, "get_collection_url", return_value="http://")
    def test_calls_request_with_post_and_collection_url(self, url_mock, request_mock):
        data = {"foo": "bar"}
        try:
            Resource.create(foo="bar")
        except APIException:
            # This is fine, just ignore it.
            pass
        request_mock.assert_called_with("post", url=url_mock.return_value, data=data)


class TestRequestMethod:

    @patch("requests.get")
    def test_params_are_passed_to_request(self, get_mock, resource):
        params = {"foo": True}
        utils.request("get", url=resource.get_absolute_url(), params=params)
        args, kwargs = get_mock.call_args
        assert kwargs["params"] == params

    @patch("requests.get")
    def test_request_calls_requests_with_specified_method(self, get_mock):
        method = "get"
        url = "foo"
        utils.request(method, url)
        get_mock.assert_called_once_with(url, verify=settings.SSL_VERIFY)
