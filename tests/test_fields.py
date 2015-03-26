import pytest
from mock import patch, Mock
from drf_client import fields
from datetime import datetime
from dateutil.tz import tzutc
from .helpers import RFC3339_TIME


@pytest.fixture
def foo():
    return 'foo'


@pytest.fixture
def bar():
    return 'bar'


def test_field_name_can_bet_set_on_init(foo):
    field = fields.Field(field_name=foo)
    assert field.field_name == foo


def test_field_name_can_be_set_through_property(bar):
    field = fields.Field()
    field.field_name = bar
    assert field.field_name == bar


def test_not_setting_field_name_raises_attribute_error_on_field_name():
    field = fields.Field()
    with pytest.raises(AttributeError):
        field.field_name


def test_not_setting_field_name_raises_attribute_error_on_source():
    field = fields.Field()
    with pytest.raises(AttributeError):
        field.source


def test_source_defaults_to_field_name_if_not_set(foo):
    field = fields.Field()
    field.field_name = foo
    assert field.source == foo


def test_setting_source_overrides_default(foo, bar):
    field = fields.Field(field_name=foo, source=bar)
    assert field.source == bar


@patch.object(fields.Field, 'get_value_from_parent')
def test_field_to_representation_calls_get_value_from_parent_correctly(get_value_mock):
    field = fields.Field()
    parent = Mock()
    field.to_representation(parent)
    get_value_mock.assert_colled_once_with(parent)


def test_field_get_value_from_parent_calls_parent_correctly_default_source(foo):
    field = fields.Field(source=foo)
    parent = Mock()
    field.get_value_from_parent(parent)
    parent._get_field_from_raw_data.assert_called_once_with(foo, caller=field)


def test_field_get_value_from_parent_calls_parent_correctly_overriden_source(foo, bar):
    field = fields.Field(source=foo)
    parent = Mock()
    field.get_value_from_parent(parent, source=bar)
    parent._get_field_from_raw_data.assert_called_once_with(bar, caller=field)


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
