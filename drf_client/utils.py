"""
drf_client SDK Utilities

Contains various utility classes and functions.
"""
import json
import requests
import pydoc
from drf_client import auth, settings
from drf_client.exceptions import APIException


def convert_to_ids(resources):
    try:
        ids = [resources.id, ]
    except AttributeError:
        # Probably a list.
        ids = [resource.id for resource in resources]

    return ids


def clamp(value, minimum=0, maximum=None):
    """Set the value to within a fixed range."""
    if maximum:
        value = min(maximum, value)

    return max(value, minimum)


def convert_from_utf8(original):
    '''Converts unicode based dict to a python str based dict.'''
    if isinstance(original, dict):
        return {convert_from_utf8(key): convert_from_utf8(value)
                for key, value in original.iteritems()}
    elif isinstance(original, list):
        return [convert_from_utf8(element) for element in original]
    elif isinstance(original, unicode):
        return original.encode('utf-8')
    else:
        return original


def parse_resources(cls, response, many=True):
    """Creates resource instances from the response.

    Raises:
        APIException -- If the response fails, the response is
            badly formatted, or if the response is missing information.

    Returns:
        A set of instantiated resources.
    """
    # from http://stackoverflow.com/questions/547829
    Parser = pydoc.locate(settings.RESPONSE_PARSER)
    resource_data = Parser().parse(response, many=many)
    if many:
        return [cls(data=data) for data in resource_data]
    else:
        return cls(data=resource_data)


class ResponseParser(object):

    def parse(self, response, many=True):
        if not response.ok:
            raise APIException("Unsuccessful response", response)

        body = response.json()
        data = self.get_data(body, many=many)
        if not data:
            raise APIException('Unable to find results', response)
        elif many and not isinstance(data, list):
            raise APIException("Response did not return a list", response)
        return data

    def get_data(self, body, many):
        if not many:
            return body

        try:
            return body['results']
        except KeyError:
            return None
