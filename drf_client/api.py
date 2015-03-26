import json
import requests
from importlib import import_module
from drf_client import settings, utils
from drf_client.exceptions import APIException


def request(method, url, **kwargs):
    """Issue the request to the API using common headers and ssl settings.

    Arguments:
        method (str): The HTTP method to use for the request (e.g. "post")
        url (str): The address for the expected resource.

    Keyword Arguments:
        params (dict): Data to provide as a parameter in the URL.
        data (dict): The data to apply to the request.

    Returns:
        Response object.
    """
    try:
        kwargs['data'] = json.dumps(kwargs['data'])
    except KeyError:
        # Not a big deal, just want it to be json if it's present.
        pass

    request = getattr(requests, method.lower())
    response = request(url, verify=settings.SSL_VERIFY, **kwargs)
    return response


def get(cls, limit=settings.MAX_PAGINATION_LIMIT, offset=0, sort="", **params):
    """Retrieve a set of resources from the API.

    Arguments:
        cls (Resource class): The resource type to retrieve
        limit (int): The maximum number of results to return.
        offset (int): Specifies the starting point for resources.
            In other words, if there's an offset of 25, it would start
            returning the 26th resource (for example).
        params (kwargs): Any additional filters and expected values.

    For example, if you'd like to set a different offset and
    specify that you're looking for a resource with a `class` of "Foo",
    you would call it directly this way::

        get(Foo, offset=25, name="foo")

    Alternatively, it's likely that there's an API method already set up
    for the resource you're trying to use. In which case,
    for the above example, you could use::

        import foos
        foos.get(name="Bar", offset=25)

    If you provide a value below 0 for `offset` or `limit`, the value
    will be reset to 0. Similarly, if a value above the
    MAX_PAGINATION_LIMIT setting is specified for `limit`, it will be reset
    to the max setting.
    """
    params['limit'] = utils.clamp(limit, maximum=settings.MAX_PAGINATION_LIMIT)
    params['offset'] = utils.clamp(offset)
    response = request("get", params=params, url=cls.get_collection_url())
    return utils.parse_resources(cls, response)


def create(cls, **data):
    """Create a single instance of a Resource.

    Arguments:
        cls (Resource class): The resource to create.

    All other keyword arguments will be provided to the request
    when POSTing. For example::

        create(Foo, name="bar", email="baz@foo.com")

    ...would try to create an instance of the Foo resource
    with a name set to "bar" and an email set to "baz@foo.com".
    """
    instance = cls()
    instance.run_validation(data)
    response = request("post", url=cls.get_collection_url(), data=data)
    try:
        return utils.parse_resources(cls=cls, response=response, many=False)
    except IndexError:
        return None
