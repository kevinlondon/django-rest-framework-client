from drf_client.exceptions import APIException
from .helpers import mock_response


def test_exception_includes_response_and_message():
    resp = mock_response(text="foo")
    msg = "Failed to do thing"
    error = APIException(msg, response=resp)
    err_str = str(error)
    assert msg in err_str
    assert "Response: foo" in err_str


def test_exception_does_not_print_body_if_no_text():
    resp = mock_response(text="")
    error = APIException("", response=resp)
    assert "Response" not in str(error)
