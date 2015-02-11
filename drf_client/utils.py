"""
drf_client SDK Utilities

Contains various utility classes and functions.
"""
import json
import requests
from drf_client import auth, settings


def issue_request(method, url, params=None, data=None, ids=None):
    """Issue the request to the API using common headers and ssl settings.

    # TODO: Update docs
    Arguments:
        method (str): The HTTP method to use for the request (e.g. "post")
        instance (Resource/Collection): The model to use for url generation.
        params (dict): Data to provide as a parameter in the URL.
        data (dict): The data to apply to the request.
        ids (list or single int): An id or ids to add to the end of the URL.

    Returns:
        Request library response.
    """
    #url = instance.get_absolute_url()
    if ids:
        url = "{0}/{1}".format(url, ",".join(str(pk) for pk in ids))

    requests_call = getattr(requests, method.lower())
    response = requests_call(url,
                             params=params,
                             data=json.dumps(data),
                             #headers=auth.get_headers(),
                             verify=settings.SSL_VERIFY)
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
