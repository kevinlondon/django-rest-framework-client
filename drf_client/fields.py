from dateutil import parser
from drf_client import settings


class Field(object):
    """A representation of an object returned by the API.

    There's a number of convenience methods associated with this to make it
    easy to use and graft on to new resources. It's mostly inspired by
    Tom Christie and co.'s work on Django Rest Framework.

    Args:
        source (str): The field in the API response to use for the field.
            By default, the source winds up being equivalent to the name
            of the field on the resource.
        required (bool): Indicates whether the field must not be blank.
    """
    _creation_counter = 0

    def __init__(self, source=None, required=False, many=False):
        self.source = source
        self.required = required
        self.many = many

    def bind(self, field_name, parent):
        """Sets the source for the field."""
        self.field_name = field_name
        self.parent = parent
        if not self.source:
            self.source = field_name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return self.to_representation()

    def to_representation(self):
        """Control how the field represents itself when called.

        When overriding Field, this is the most likely candidate for change.
        """
        return self._get_value()

    def _get_value(self, source=None):
        """Retrieve the value from the parent's information.

        The parent may need to fetch data from the API if it's not stored
        locally or if it's stale.
        """
        if not source:
            source = self.source

        return self.parent._get_field_from_raw_data(source)

    def _get_key_or_none(self, target, key):
        """Helper to return the id value or None on non required properties"""
        try:
            return target.get(key)
        except AttributeError:
            return None


class DateTimeField(Field):

    def to_representation(self):
        date = self._get_value()
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

    def to_representation(self):
        links = self._get_value(source="links")
        link_key = self.source.rstrip("_link")
        return self._get_key_or_none(links, link_key)
