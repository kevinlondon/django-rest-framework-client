from dateutil import parser
from drf_client import settings


class Field(object):
    """A representation of an object returned by the API.

    There's a number of convenience methods associated with this to make it
    easy to use and graft on to new resources. It's mostly inspired by
    Tom Christie and co.'s work on Django Rest Framework.

    Args:
        field_name (str): The field name on the parent instance that
            corresponds to this Field.
        source (str): The field in the API response to use for the field.
            By default, the source winds up being equivalent to the name
            of the field on the resource.
        required (bool): Indicates whether the field must not be blank.
    """
    _creation_counter = 0

    def __init__(self, field_name=None, source=None, required=False):
        self.required = required
        self._field_name = field_name
        self._source = source

    @property
    def field_name(self):
        if not self._field_name:
            raise AttributeError('field_name is unset.')
        return self._field_name

    @field_name.setter
    def field_name(self, value):
        self._field_name = value

    @property
    def source(self):
        if self._source:
            return self._source
        return self.field_name

    def __get__(self, instance, owner):
        """Descriptor 'magic_method' for retrieving this Fields value.

        When attached as a descriptor in a class definition:

        class MyResource(Resource):
            workflow = field.Field()

        This is the method called to retrieve the value when workflow is called.
        Fields are always assumed to be attached to a parent Resource, which
        will correspond to the 'instance' in this methods signature. Owner
        refers to the parent instances class, and only comes into play when
        workflow is called on the parent Class directly.
        """
        if instance is None:
            # Not called through a parent instance, so return itself
            return self

        # Get your field value from the attached parent
        return self.to_representation(instance)

    def to_representation(self, parent):
        """Format and retrieve the representation of this object.

        Gets the value from the attached parent and returns it. This is
        provided as a seam for subclassing as additional processing can
        easily be inserted.

        Args:
            parent (Resource): The parent resource to perform the data
                lookup on.

        Returns:
            (varies): Representation of this Fields data.
        """
        return self.get_value_from_parent(parent)

    def get_value_from_parent(self, parent, source=None, *args, **kwargs):
        """Retrieve the value from the parent's information.

        The parent may need to fetch data from the API if it's not stored
        locally or if it's stale.

        Args:
            parent (Resource): The parent this field is attached to.
            source (str): Optional source field_name to useful for
                customization in source classes
        """
        if not source:
            source = self.source

        return parent._get_field_from_raw_data(source, caller=self)

    def _get_key_or_none(self, target, key):
        """Helper to return the id value or None on non required properties"""
        try:
            return target.get(key)
        except AttributeError:
            return None


class DateTimeField(Field):

    def to_representation(self, parent):
        date = self.get_value_from_parent(parent)
        return self.to_datetime(date)

    @classmethod
    def to_datetime(cls, original_date):
        """Convert a date into a Python datetime object.

        Arguments:
            original_date (str or int timestamp): The date to convert.
        """
        if not original_date:
            return None

        try:
            dt = parser.parse(original_date)
        except AttributeError:
            msg = "Invalid date format provided: {0}".format(original_date)
            raise TypeError(msg.format(dt_format=settings.DATETIME_FORMAT))

        return dt


class LinkField(Field):

    def to_representation(self, parent):
        links = self.get_value_from_parent(parent, source="links")
        link_key = self.source.rstrip("_link")
        return self._get_key_or_none(links, link_key)
