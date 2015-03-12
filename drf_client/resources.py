# coding=utf-8
"""
drf_client SDK: Resource

The abstract class for Resources in the drf_client System.
All Resources (e.g., projects, assets, users) subclass from this.
"""

import importlib
import pprint

from collections import OrderedDict
from datetime import datetime, timedelta
from weakref import WeakKeyDictionary

from . import settings
from .exceptions import APIException
from .utils import convert_from_utf8, clamp, request
from .fields import Field
from .mixins import CreateMixin, GetMixin


class DeprecatedCollection(object):
    def format_data(self, data):
        """Shuffles around fields, if needed, to provide additional data.

        In addition, this will also transform resources into their primary
        key values.
        """
        for key, value in data.iteritems():
            if isinstance(value, Resource):
                data[key] = value.id


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


class Resource(CreateMixin, GetMixin, Field):

    __metaclass__ = ResourceMetaclass
    _route = ""  # To be overridden by subclasses
    DATA_EXPIRATION = timedelta(minutes=2)

    def __init__(self, id=None, data=None, parent=None, *args, **kwargs):
        """Instantiates a drf_client resource.

        The resource performs deferred loading, so no data
        will be actually be loaded until a property on the object is
        accessed.

        Keyword Arguments:
            id (int): The resource's primary key (id)
            data (dict): A dict of the Resources data. There should be a
                loose connection between the data's keys and the Resources
                Fields.
            parent (instance): The parent Resource/ListResource that created
                this object. Not always necessary.
        """
        super(Resource, self).__init__(*args, **kwargs)
        self._id = id
        self.raw_data = data
        self._parent = parent
        self._set_field_names()

    def __new__(cls, *args, **kwargs):
        # Override the new to create `ListResource` classes instead when
        # `many = True` is set. Pulled from DRF BaseSerializer/ListSerializer.
        if kwargs.pop('many', False):
            return cls.many_init(*args, **kwargs)
        return super(Resource, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def many_init(cls, *args, **kwargs):
        """Initializes a ListResource.

        This method initializes a `ListResource` parent class when `many=True`
        is used on an attached Resource definition. If you need to customize
        the arguments used to create a `ListResource`, this is where you
        would do it.
        """
        child_resource = cls(*args, **kwargs)
        list_kwargs = {'child_resource': child_resource}
        list_kwargs.update(kwargs)
        # If we end up needing to customize ListResources in the future, this
        # is where we would pull the `list_resource_class` needed
        return ListResource(*args, **list_kwargs)

    def __repr__(self):
        if self.raw_data:
            return '{0}({1})'.format(self.__class__.__name__,
                                     pprint.pformat(self.raw_data))
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

    def __get__(self, instance, owner):
        """The get for a Resource attached as a descriptor.

        If this is called, it can be assumed to be attached to another Resource.
        In that instance, the resource should utilize it's parent Resource to
        retrieve it's data. If it has already been loaded with data, return
        itself.
        """
        if not instance:
            return self

        # Create a new instance of this Resource with the data pulled from
        # it's parent. This must be done to avoid affecting other instances
        # of attached Resources when storing the data directly on self
        parent_data = self.get_value_from_parent(instance, caller=self)

        return type(self)(data=parent_data, parent=instance,
                          field_name=self.field_name)

    def _set_field_names(self):
        """Set the field_name on each field to it's label on the Resource."""
        for fieldname, fieldtype in self._declared_fields.iteritems():
            fieldtype.field_name = fieldname

    def run_validation(self, data):
        self._validate_fields(data)
        self.validate(data)

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
        """Clears the data on the object and pulls new data from the API.

        Raises:
            LookupError: If the data retrieved is not for the id of this
                Resource.
        """
        data = self.fetch_data()
        # Verify the data didn't change under us
        if data['id'] != self.id:
            raise LookupError('Did not find data for {}'.format(self.__str__()))
        self.raw_data = data

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

    @classmethod
    def get_collection_url(cls):
        """Return the base collection url."""
        return "{0}/{1}".format(settings.API_URL, cls._route)

    def get_absolute_url(self):
        """Return the canonical API url for the resource."""
        return "{0}/{1}".format(self.get_collection_url(), self.id)

    def delete(self):
        """Removes the resource by calling the API.

        Raises:
            RequestException: If there's a problem with the request.
        """
        response = request("delete", url=self.get_absolute_url())
        if not response.ok:
            raise APIException("Could not delete %s" % self, response=response)

    def fetch_data(self):
        """GET the resource information from the API based on its primary key,
        unless the Resource has a parent resource.

        Retrieves the raw json body data from the response on resource GET.

        Returns:
            JSON representation of the resource.

        Raises:
            APIException -- If the request fails for some reason.
        """
        if self._parent:
            # If it has a parent instance, refer to that for it's data
            data = self.get_value_from_parent(self._parent)
        else:
            response = issue_request("get", url=self.get_absolute_url())
            data = self.collection._extract_resource_data(response)[0]
        return data

    def _get_field_from_raw_data(self, fieldname, *args, **kwargs):
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

        return self.raw_data.get(fieldname)

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


class ListResource(Field):
    """
    ListResource is automatically inserted to replace any field created
    with the `many=True` kwarg. The ListResource records the type of Field that
    was desired, and then uses that information to create children instances
    for the list of data in that location.

    Since the ListResource serves as intermediary between all the parent and
    children it keep an internal `relationships` mapping to know which parent
    it needs to access for data when one of the children attempts to reload.
    """

    def __init__(self, *args, **kwargs):
        """Initializes a new ListResource.

        Keyword Arguments:
            child_resource (varies): An instance of the class to use when
                creating children Resources.
        """
        self.child_resource = kwargs.pop('child_resource')
        super(ListResource, self).__init__(*args, **kwargs)
        self.relationships = WeakKeyDictionary()

    def to_representation(self, parent):
        """Formats and retrieve the representation of all children objects.

        This method retrieves all the data_set for this field from the parent,
        and then creates a new instance of `child_resource` for each set of
        data in the data_set. It then records the parent and associated
        children in an internal relationships map it uses when children try to
        refresh their data later.
        """
        parent_data = self.get_value_from_parent(parent)
        klass = type(self.child_resource)
        children = [klass(data=data, parent=self, field_name=self.field_name)
                    for data in parent_data]
        self.relationships[parent] = children
        return children

    def _get_field_from_raw_data(self, fieldname, caller=None, *args, **kwargs):
        """Pulls the fieldname data from the associated parent.

        Determines the correct parent for the calling instance. It then loads
        the data from that parent for this field, and attempts to find data
        with a matching id.

        Args:
            fieldname (str): The key for the desired information.

        Keyword Arguments:
            caller (instance): The instance that called this method. Used
                to determine which parent should be called for the data lookup.

        Raises:
            LookupError: If there is no data to associate with the calling
                instance.

        Return:
            The raw data value for the calling instance.
        """
        parent = self._get_associated_parent(caller)

        data_set = self.get_value_from_parent(parent)

        for data in data_set:
            if caller.id == data['id']:
                return data

        raise LookupError('Did not find data for {}'.format(str(caller)))

    def _get_associated_parent(self, caller):
        """Retrieves the parent associated with the calling instance.

        Raises:
            LookupError: If no associated parent is found.
        """
        for parent in self.relationships:
            if caller in self.relationships[parent]:
                return parent
        msg = 'Unable to find associated parent for one of many {}'
        raise LookupError(msg.format(str(caller)))
