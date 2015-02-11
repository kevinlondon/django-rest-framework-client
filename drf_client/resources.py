# coding=utf-8
"""
drf_client SDK: Resource

The abstract class for Resources in the drf_client System.
All Resources (e.g., projects, assets, users) subclass from this.
"""
import json
import importlib
import pprint
from collections import OrderedDict
from datetime import datetime, timedelta

from drf_client import settings
from drf_client.exceptions import APIException
from drf_client.utils import convert_from_utf8, issue_request, clamp
from drf_client.fields import Field


def delete(path, *args, **kwargs):
    print("Calling delete")
    pass


def create(path, *args, **kwargs):
    print("Calling post on {0}".format(path))
    return model()


def update(path, *args, **kwargs):
    print("Calling put on {0}".format(path))
    pass


def get(path, *args, **kwargs):
    print("Calling get on {0}".format(path))
    url = "{api}/{path}".format(api=settings.API_URL, path=path)
    return issue_request("get", url)


def parse(response, model):
    """Return instances of the objects requested."""
    body = json.loads(response.content)
    instances = [model(data=instance_data) for instance_data in body['results']]
    return instances


class Collection(object):

    collection_name = ""  # override. eg: "assets", "projects"
    resource = ""  # override. e.g. "Asset", "Project"

    @property
    def resource_class(self):
        """Dynamically load the related resource class."""
        if not hasattr(self, "_resource_class"):
            module = importlib.import_module(self.__module__)
            self._resource_class = getattr(module, self.resource)

        return self._resource_class

    def get_absolute_url(self):
        return "{0}/{1}".format(settings.API_URL, self.collection_name)

    def _parse_resources(self, response):
        """Creates resource instances from the response.

        Raises:
            APIException -- If the response fails, the response is
                badly formatted, or if the response is missing information.
        """
        resource_data = self._extract_resource_data(response)
        resources = [self.resource_class(data=data) for data in resource_data]
        if not resources:
            msg = "No {} found in response.".format(self.collection_name)
            raise APIException(msg, response)
        return resources

    def _parse_resource(self, response):
        """Parse the first resource from the given response.

        """
        return self._parse_resources(response)[0]

    def _extract_resource_data(self, response):
        """Parses all of the raw resource data from the response."""
        if not response.ok:
            msg = "Unable to parse %s." % self.collection_name
            raise APIException(msg, response)

        body = response.json()
        try:
            data = body['results'][self.collection_name]
        except KeyError:
            msg = ('Unable to find the %s data in the response. '
                   'The response appears malformed.' % self.collection_name)
            raise APIException(msg, response)

        return data

    def create_resource(self, data):
        self.format_data(data)
        resource_data = self.post(data)
        return self.resource_class(data=resource_data)

    def format_data(self, data):
        """Shuffles around fields, if needed, to provide additional data.

        In addition, this will also transform resources into their primary
        key values.
        """
        for key, value in data.iteritems():
            if isinstance(value, Resource):
                data[key] = value.id

    def post(self, data):
        """Creates new resource by posting information to the API.

        Returns:
            The resource object.
        """
        response = issue_request("post", data=data, instance=self)
        return self._extract_resource_data(response)[0]

    def get(self, limit=25, offset=0, sort="", **params):
        """Retrieve a set of resources from the API.

        Arguments:
            limit (int): The maximum number of results to return.
            offset (int): Specifies the starting point for resources.
                In other words, if there's an offset of 25, it would start
                returning the 26th resource (for example).
            sort (str): The field in which the results should be sorted.
                As per the API, it should be prepended with a `+` if it is
                ascending and `-` if it's descending. If there's no sign
                specified, it will default to `+` (ascending). If it's left
                empty, the API will use the default sort for the resources.
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
        if sort and sort[0] not in ("-", "+"):
            sort = "+{}".format(sort)

        params['limit'] = clamp(limit, maximum=settings.MAX_PAGINATION_LIMIT)
        params['offset'] = clamp(offset)
        params['sort'] = sort
        response = issue_request("get", params=params, instance=self)
        return self._parse_resources(response)


class SubCollection(Collection):

    def _bind(self, parent):
        self.parent = parent

    def get_absolute_url(self):
        base = self.parent.get_absolute_url()
        return "{0}/{1}".format(base, self.collection_name)


class ResourceMetaclass(type):
    """
    This metaclass sets a dictionary named `_declared_fields` on the class.
    Any instances of `Field` included as attributes on either the class
    or on any of its superclasses will be include in the
    `_declared_fields` dictionary.

    Copied from Django Rest Framework's implementation:

        https://github.com/tomchristie/django-rest-framework/blob/ \
            master/rest_framework/serializers.py
    """

    @classmethod
    def _get_declared_fields(cls, bases, attrs):
        fields = [(field_name, attrs[field_name])
                  for field_name, obj in list(attrs.items())
                  if isinstance(obj, Field)]
        fields.sort(key=lambda x: x[1]._creation_counter)

        # If this class is subclassing another Resource, add that Resource's
        # fields.  Note that we loop over the bases in *reverse*. This is necessary
        # in order to maintain the correct order of fields.
        for base in bases[::-1]:
            if hasattr(base, '_declared_fields'):
                fields = list(base._declared_fields.items()) + fields

        return OrderedDict(fields)

    def __new__(cls, name, bases, attrs):
        attrs['_declared_fields'] = cls._get_declared_fields(bases, attrs)
        return super(ResourceMetaclass, cls).__new__(cls, name, bases, attrs)


class Resource(Field):

    __metaclass__ = ResourceMetaclass
    collection = Collection()  # Should be overridden by subclasses
    DATA_EXPIRATION = timedelta(minutes=2)

    def __init__(self, id=None, data=None, *args, **kwargs):
        """Instantiates a drf_client resource.

        The resource performs deferred loading, so no data
        will be actually be loaded until a property on the object is
        accessed.

        Keyword Arguments:
            id (int): The resource's primary key (id)
        """
        super(Resource, self).__init__(*args, **kwargs)
        self._id = id
        self.raw_data = data
        self._bind_fields()

    def __repr__(self):
        if self._data_store:
            return '{0}({1})'.format(self.__class__.__name__,
                                     pprint.pformat(self._data_store))
        else:
            return '{0} - Not Loaded '.format(self.__str__())

    def __str__(self):
        return '{0}(id={1})'.format(self.__class__.__name__, self.id)

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return False
        try:
            if self.id != other.id:
                return False
        except AttributeError:
            return False
        return True

    @classmethod
    def create(cls, **data):
        """Perform full validation and then have the collection create it."""
        instance = cls()
        instance.run_validation(data)
        return instance.collection.create_resource(data)

    def _bind_fields(self):
        """Attach the class' fields to the resource as attributes."""
        for fieldname, fieldtype in self._declared_fields.iteritems():
            fieldtype.bind(fieldname, parent=self)

    def run_validation(self, data):
        self._validate_fields(data)
        self.validate(data)

    def to_representation(self):
        # Always pull the latest data from the parent
        self.raw_data = self._get_value()
        return self

    def _validate_fields(self, data):
        """Validate each required field on the resource."""
        for fieldname, fieldtype in self._declared_fields.iteritems():
            value = data.get(fieldname)
            if fieldtype.required and not value:
                raise ValueError("No value provided for '{0}'".format(fieldname))

            try:
                validate = getattr(self, "validate_{0}".format(fieldname))
            except AttributeError:
                # No validation specifically available for field.
                pass
            else:
                validate(value)

    def validate(self, data):
        """Override this."""
        pass

    def reload(self):
        """Clears the data on the object and pulls new data from the API"""
        self.raw_data = self.fetch_data()

    @property
    def id(self):
        if self.raw_data:
            self._id = self.raw_data['id']

        return self._id

    @property
    def raw_data(self):
        return self._data_store

    @raw_data.setter
    def raw_data(self, data):
        self._last_loaded = datetime.now() if data else None
        self._data_store = convert_from_utf8(data)

    def get_absolute_url(self):
        """Return the canonical API url for the resource."""
        return "{0}/{1}".format(self.collection.get_absolute_url(), self.id)

    def delete(self):
        """Removes the resource by calling the API.

        Raises:
            RequestException: If there's a problem with the request.
        """
        response = issue_request("delete", instance=self)
        if not response.ok:
            raise APIException("Could not delete %s" % self, response=response)

    def fetch_data(self):
        """GET the resource information from the API based on its primary key.

        Retrieves the raw json body data from the response on resource GET.

        Returns:
            JSON representation of the resource.

        Raises:
            APIException -- If the request fails for some reason.
        """
        response = issue_request("get", instance=self)
        return self.collection._extract_resource_data(response)[0]

    def _get_field_from_raw_data(self, fieldname):
        """Pulls the fieldname from the stored data.

        Finds the raw data for the given fieldname key. If no data has been
        loaded yet, load the data for the object first. If data has been
        previously loaded, confirm that the loading time is not outside the
        dirty data time limit. If so, also reload the data.

        Args:
            fieldname (str): The key for the desired information.

        Raises:
            LookupError: If the given fieldname is not found in the current data.

        Return:
            The raw data value for the desired fieldname key.
        """
        if (self.raw_data and self._is_data_stale()) or not self.raw_data:
            self.reload()

        if fieldname and fieldname not in self.raw_data:
            msg = "No '%s' field found on the resource. Available fields: %s"
            fields = ", ".join(field for field in self.raw_data.keys())
            raise LookupError(msg % (fieldname, fields))

        return self._data_store.get(fieldname)

    def _is_data_stale(self):
        """Checks to see if the data was last loaded over a set time limit.

        The time limit is set on the resource itself. If the data is older
        than the time limit, the next time a property is accessed all the data
        for the object will be reloaded.

        Returns:
            True is the data is outside the time limit (stale), False if not.
        """
        expiration = self.__class__.DATA_EXPIRATION
        return (datetime.now() - self._last_loaded) > expiration

    def _extract_location_from_response_headers(self, response):
        """Extracts the url from the location header on the response.

        Confirms the response from the upload url creation was good and pulls
        the upload url from the response headers.

        Args:
          response (requests.Response) -- Response to parse

        Returns:
          url from the location header.

        Raises:
          APIException -- If the request response indicates failure,
            or if the resource upload url cannot be pulled from the response
            headers.
        """
        if not response.ok:
            raise APIException("Could not retrieve location header.", response)

        url = response.headers.get('Location')
        if not url:
            msg = "No valid location found in response headers: {0}"
            raise APIException(msg.format(response.headers), response)

        return url
