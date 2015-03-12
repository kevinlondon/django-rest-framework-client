import pytest
from mock import patch
from datetime import timedelta

from drf_client.resources import Resource
from drf_client.exceptions import APIException
from drf_client import fields, settings, resources
from .helpers import mock_response
from .fixtures import authenticate

ROUTE = "foo"

class ExampleResource(Resource):
    _route = ROUTE

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


def test_fields_embedded_on_the_resource(resource):
    res_fields = resource._declared_fields
    assert isinstance(res_fields['basic'], fields.Field)
    assert isinstance(res_fields['example_link'], fields.LinkField)


def test_bind_fields_assigns_attr_to_resource(resource):
    resource = ExampleResource()
    value = "foo"
    with patch.object(fields.Field, "__get__") as rep_mock:
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


def test_get_collection_url_includes_route_and_api_url():
    actual_url = ExampleResource.get_collection_url()
    expected_url = "{0}/{1}".format(settings.API_URL, ROUTE)
    assert actual_url == expected_url


def test_get_absolute_url_includes_id(resource):
    with patch.object(resource, "get_collection_url") as collection_url:
        collection_url.return_value = "resource"
        resource._id = 10
        url = resource.get_absolute_url()
        assert url == "resource/10"


@patch("requests.delete")
def test_delete_calls_api(delete_mock, resource, authenticate):
    delete_mock.return_value = mock_response(ok=True)
    resource.delete()
    assert delete_mock.called
    url = delete_mock.call_args[0][0]
    assert url == resource.get_absolute_url()


@patch("requests.delete")
def test_delete_raises_request_exception_on_error(delete_mock, resource, authenticate):
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


class SimpleResource(Resource):
    name = fields.Field()


class ParentResource(Resource):
    name = fields.Field()
    brother = SimpleResource()
    sister = SimpleResource()
    children = SimpleResource(many=True)


def simple_resource(id=1, name='simple'):
    return {'id': id, 'name': name}


@pytest.fixture
def parent_resource_data():
    return {'id': 1,
            'name': 'Mother',
            'brother': simple_resource(2, 'Bob'),
            'sister': simple_resource(2, 'Mary'),
            'children': [simple_resource(3, 'Jason'),
                         simple_resource(4, 'Ken')]}


@pytest.fixture
def parent_resource_reload_data():
    return {'id': 1,
            'name': 'Father',
            'brother': simple_resource(2, 'Marley'),
            'sister': simple_resource(5, 'Jane'),
            'children': [simple_resource(3, 'Jenny'),
                         simple_resource(5, 'Stan')]}


@pytest.fixture
def force_reload(request):
    # Triggers continuous reload of Resources
    previous = Resource.DATA_EXPIRATION
    Resource.DATA_EXPIRATION = timedelta(0)

    def fix():
        Resource.DATA_EXPIRATION = previous

    request.addfinalizer(fix)


@pytest.fixture
def parent_resource():
    return ParentResource(id=1)


@patch.object(ParentResource, 'fetch_data')
def test_resource_reloads_data_correctly(
        fetch_mock, parent_resource_data, parent_resource_reload_data,
        force_reload, parent_resource):
    # First data set
    fetch_mock.return_value = parent_resource_data
    assert parent_resource.name == 'Mother'
    # Second data set
    fetch_mock.return_value = parent_resource_reload_data
    assert parent_resource.name == 'Father'


@patch.object(ParentResource, 'fetch_data')
def test_resource_on_resource_reloads_data_correctly_with_same_id(
        fetch_mock, parent_resource_data, parent_resource_reload_data,
        force_reload, parent_resource):
    fetch_mock.return_value = parent_resource_data
    assert parent_resource.brother.name == 'Bob'
    fetch_mock.return_value = parent_resource_reload_data
    assert parent_resource.brother.name == 'Marley'


@patch.object(ParentResource, 'fetch_data')
def test_resource_on_resource_reloads_data_correctly_regardless_of_id(
        fetch_mock, parent_resource_data, parent_resource_reload_data,
        force_reload, parent_resource):
    fetch_mock.return_value = parent_resource_data
    assert parent_resource.sister.id == 2
    assert parent_resource.sister.name == 'Mary'
    fetch_mock.return_value = parent_resource_reload_data
    # Ok if the attached value changes
    assert parent_resource.sister.id == 5
    assert parent_resource.sister.name == 'Jane'


@patch.object(ParentResource, 'fetch_data')
def test_resource_on_resource_reloads_data_correctly_when_detached(
        fetch_mock, parent_resource_data, parent_resource_reload_data,
        force_reload, parent_resource):
    fetch_mock.return_value = parent_resource_data
    # Detach Sub Resource
    brother = parent_resource.brother
    assert brother.name == 'Bob'
    fetch_mock.return_value = parent_resource_reload_data
    assert brother.name == 'Marley'


@patch.object(ParentResource, 'fetch_data')
def test_resource_on_resource_errors_on_reload_when_no_data_and_detached(
        fetch_mock, parent_resource_data, parent_resource_reload_data,
        force_reload, parent_resource):
    fetch_mock.return_value = parent_resource_data
    sister = parent_resource.sister
    assert sister.name == 'Mary'
    fetch_mock.return_value = parent_resource_reload_data
    with pytest.raises(LookupError) as e:
        # Should error, since resource no longer exists in parent data
        sister.name
    assert 'Did not find data for SimpleResource(id=2)' in str(e)


@patch.object(ParentResource, 'fetch_data')
def test_one_of_many_on_resource_reloads_data_correctly(
        fetch_mock, parent_resource_data, parent_resource_reload_data,
        force_reload, parent_resource):
    fetch_mock.return_value = parent_resource_data
    first_child = parent_resource.children[0]
    assert first_child.id == 3
    assert first_child.name == 'Jason'
    fetch_mock.return_value = parent_resource_reload_data
    assert first_child.id == 3
    assert first_child.name == 'Jenny'


@patch.object(ParentResource, 'fetch_data')
def test_one_of_many_on_resource_errors_when_id_no_longer_exists(
        fetch_mock, parent_resource_data, parent_resource_reload_data,
        force_reload, parent_resource):
    fetch_mock.return_value = parent_resource_data
    first_child = parent_resource.children[1]
    assert first_child.id == 4
    assert first_child.name == 'Ken'
    fetch_mock.return_value = parent_resource_reload_data
    with pytest.raises(LookupError) as e:
        first_child.name
    assert 'Did not find data for {}'.format(str(first_child)) in str(e)
