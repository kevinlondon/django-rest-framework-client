"""
drf_client SDK Utilities

Contains various utility classes and functions.
"""
import json
import requests
from drf_client import auth, settings
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
                      #headers=auth.get_headers(),
    return response


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
    resource_data = ResponseParser().parse(response, many=many)
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
        elif not isinstance(data, list):
            raise APIException("Response did not return a list", response)
        return data

    def get_data(self, body, many):
        if not many:
            return body

        try:
            return body['results']
        except KeyError:
            return None
