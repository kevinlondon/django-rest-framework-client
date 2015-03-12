from importlib import import_module
from drf_client import settings
from drf_client.utils import clamp, request, parse_resources
from drf_client.exceptions import APIException


class GetMixin(object):

    @classmethod
    def get(cls, limit=25, offset=0, sort="", **params):
        """Retrieve a set of resources from the API.

        Arguments:
            limit (int): The maximum number of results to return.
            offset (int): Specifies the starting point for resources.
                In other words, if there's an offset of 25, it would start
                returning the 26th resource (for example).
            params (kwargs): Any additional filters and expected values.

        For example, if you'd like to set a different offset and
        specify that you're looking for a resource with a `name` of "foo",
        you would call it this way::

            collection = Collection()
            collection.get(offset=25, name="foo")

        If you provide a value below 0 for `offset` or `limit`, the value
        will be reset to 0. Similarly, if a value above the
        MAX_PAGINATION_LIMIT setting is specified for `limit`, it will be reset
        to the max setting.
        """
        params['limit'] = clamp(limit, maximum=settings.MAX_PAGINATION_LIMIT)
        params['offset'] = clamp(offset)
        response = request("get", params=params, url=cls.get_collection_url())
        return parse_resources(cls, response)


class CreateMixin(object):

    @classmethod
    def create(cls, **data):
        instance = cls()
        instance.run_validation(data)
        response = request("post", url=cls.get_collection_url(), data=data)
        try:
            return parse_resources(cls=cls, response=response, many=False)
        except IndexError:
            return None
