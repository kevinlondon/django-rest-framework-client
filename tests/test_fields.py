import pytest
from mock import patch, Mock
from drf_client import fields
from datetime import datetime
from dateutil.tz import tzutc
from .helpers import RFC3339_TIME


def test_field_binding_sets_source_if_not_set():
    field = fields.Field()
    field.bind("foo", parent=None)
    assert field.source == "foo"


def test_field_binding_does_not_source_if_set():
    field = fields.Field(source="bar")
    field.bind("foo", parent=None)
    assert field.source == "bar"


def test_field_binding_sets_fieldname():
    field = fields.Field(source="bar")
    field.bind("foo", parent=None)
    assert field.field_name == "foo"


def test_link_field_strips_off_link_descriptor():
    field = fields.LinkField()
    field.bind(field_name="created_by_link", parent=None)
    assert field.source == "created_by_link"
    field._get_value = Mock(return_value={"created_by": "foo"})
    assert field.to_representation() == "foo"


def test_datetime_field_converts_rfc3339_to_datetime():
    field = fields.DateTimeField()
    converted_dt = field.to_datetime(RFC3339_TIME)
    assert isinstance(converted_dt, datetime)
    assert converted_dt.tzinfo == tzutc()


def test_datetime_field_cannot_convert_timestamp_to_datetime():
    field = fields.DateTimeField()
    with pytest.raises(TypeError):
        field.to_datetime(1421112709)


def test_datetime_field_returns_none_when_converting_none_to_dt():
    field = fields.DateTimeField()
    converted_dt = field.to_datetime(None)
    assert converted_dt is None


def test_required_flag_set_on_init():
    field = fields.Field()
    assert field.required is False


def test_required_flag_set_manually_on_init():
    field = fields.Field(required=True)
    assert field.required is True
