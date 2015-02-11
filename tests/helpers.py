from mock import Mock, patch
from drf_client.resources import Resource

RFC3339_TIME = "2015-01-17T01:53:36Z"


def mock_response(ok=True, reason='', text='', body='', headers='',
                  json_value={}):
    response = Mock()
    response.ok = ok
    response.reason = reason
    response.text = text
    response.body = body
    response.headers = headers
    response.json.return_value = json_value
    return response


class BaseResourceTest(object):

    ResourceClass = None

    def test_properties_are_mapped_to_object(self, example_resource_data):
        with patch.object(self.ResourceClass, 'fetch_data') as request_mock:
            request_mock.return_value = example_resource_data
            resource_class = self.ResourceClass(example_resource_data['id'])
            for key, value in example_resource_data.iteritems():
                if key == "links":
                    for link_key, link_value in value.iteritems():
                        link_attr = getattr(resource_class, "{0}_link".format(link_key))
                        assert link_attr == link_value
                else:
                    actual_value = getattr(resource_class, key)
                    if key.startswith("date"):
                        assert actual_value is not None
                    elif isinstance(actual_value, Resource):
                        assert actual_value.id == value['id']
                    else:
                        assert actual_value == value
