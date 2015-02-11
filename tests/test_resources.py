import mock
from mock import patch
import pytest
from drf_client.resources import Resource, Collection
from drf_client.exceptions import APIException
from drf_client import fields, settings
from .helpers import mock_response


class ExampleResource(Resource):
    basic = fields.Field()
    example_link = fields.LinkField()


class ChildExampleResource(ExampleResource):
    pass


class DifferentResource(Resource):
    basic = fields.Field()
    example_link = fields.LinkField()


@pytest.fixture
def resource():
    return ExampleResource()


@pytest.fixture
def id_resource():
    return ExampleResource(id=1)


def test_fields_embedded_on_the_resource():
    resource = ExampleResource()
    res_fields = resource._declared_fields
    assert isinstance(res_fields['basic'], fields.Field)
    assert isinstance(res_fields['example_link'], fields.LinkField)


def test_bind_fields_assigns_attr_to_resource():
    resource = ExampleResource()
    value = "foo"
    with mock.patch.object(fields.Field, "__get__") as rep_mock:
        rep_mock.return_value = value
        assert resource.basic == value
        assert resource.example_link == value


def test_extract_location_from_headers_errors_on_failed_request(resource):
    response = mock_response(ok=False)
    with pytest.raises(APIException) as err:
        resource._extract_location_from_response_headers(response)
    assert 'Could not retrieve location header' in str(err)


def test_resource_name_sets_name_based_on_class(resource):
    assert str(resource).startswith("ExampleResource")


def test_resource_name_when_loaded_based_on_class(resource):
    resource._data_store = True
    assert repr(resource).startswith("ExampleResource")


@patch.object(ExampleResource, "run_validation")
@patch.object(ExampleResource.collection, "create_resource")
def test_create_call_hits_validation_and_post(post_mock, validate_mock):
    ExampleResource.create()
    validate_mock.assert_called_with({})
    assert post_mock.called


@patch.object(ExampleResource, "validate")
def test_validation_gets_called_with_args(validate_mock, resource):
    data = {"name": "foo"}
    resource.run_validation(data)
    validate_mock.assert_called_with(data)


@patch('requests.get')
@patch.object(Collection, '_parse_resource')
def test_resource_fetch_data_uses_correct_ssl_setting(collection_mock, request_mock, resource):
    for setting in (True, False):
        settings.SSL_VERIFY = setting
        resource.fetch_data()
        (_, called_kwargs) = request_mock.call_args
        assert called_kwargs['verify'] == setting


def test_setting_raw_data_updates_data_store(resource):
    example_dict = {"foo": "bar"}
    resource.raw_data = example_dict
    assert resource.raw_data['foo'] == "bar"
    assert resource._last_loaded is not None
    assert resource._data_store == example_dict


def test_id_can_pull_from_data_store_if_not_assigned_directly(resource):
    resource.raw_data = {"id": 10}
    assert resource.id == 10


def test_id_is_none_if_no_data_store_set(resource):
    resource.raw_data = None
    assert resource.id is None


def test_id_sets_properly_if_specified_on_creation():
    resource = ExampleResource(id=10)
    assert resource.id == 10


def test_get_absolute_url_includes_id(resource):
    with patch.object(resource.collection, "get_absolute_url") as collection_url:
        collection_url.return_value = "resource"
        resource._id = 10
        url = resource.get_absolute_url()
        assert url == "resource/10"


@patch("requests.delete")
def test_delete_calls_api(delete_mock, resource):
    delete_mock.return_value = mock_response(ok=True)
    resource.delete()
    assert delete_mock.called
    url = delete_mock.call_args[0][0]
    assert url == resource.get_absolute_url()


@patch("requests.delete")
def test_delete_raises_request_exception_on_error(delete_mock, resource):
    delete_mock.return_value = mock_response(ok=False)
    with pytest.raises(APIException) as err:
        resource.delete()

    assert "Could not delete" in str(err)


def test_can_set_raw_data_on_initialization():
    data = {"id": 20, "name": "foo"}
    resource = Resource(data=data)
    assert resource.raw_data == data


def test_setting_raw_data_to_none_does_not_set_updated():
    resource = Resource(data=None)
    assert resource._data_store is None
    assert not resource._last_loaded


def test_resources_with_same_ids_are_equal(id_resource):
    second_resource = ExampleResource(id=id_resource.id)
    assert id_resource == second_resource


def test_resources_with_different_ids_are_not_equal(id_resource):
    second_resource = ExampleResource(id=(id_resource.id + 1))
    assert id_resource != second_resource


def test_resources_with_same_ids_different_types_not_equal(id_resource):
    different_resource = DifferentResource(id=id_resource.id)
    assert id_resource != different_resource


def test_descendent_resource_not_equal_to_parent_resource(id_resource):
    child_resource = ChildExampleResource(id=id_resource.id)
    assert child_resource != id_resource


def test_parent_resource_not_equal_to_descendent_resource(id_resource):
    child_resource = ChildExampleResource(id=id_resource.id)
    assert id_resource != child_resource


def test_id_resets_when_raw_data_changes():
    old_id = 4
    data = {"id": old_id}
    resource = Resource(data=data)
    assert resource.id == old_id

    new_id = 7000
    resource.raw_data = {"id": new_id}
    assert resource.id == new_id


def test_id_does_not_cause_error_if_not_loaded():
    resource = Resource()
    assert resource.id is None
