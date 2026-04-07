from pleasant_errors import Error, StructuredError


def test_app_error_fields():
    full = Error(message="something failed", code="DB_1045", context={"table": "users"})
    assert full.message == "something failed"
    assert full.code == "DB_1045"
    assert full.context == {"table": "users"}

    minimal = Error(message="oops", code="VALUEERROR")
    assert minimal.message == "oops"
    assert minimal.code == "VALUEERROR"
    assert minimal.context == {}


def test_structured_error_protocol_satisfied():
    class MyError(Exception):
        @property
        def error_code(self) -> str:
            return "MY_001"

        @property
        def context(self) -> dict:
            return {"key": "value"}

    assert isinstance(MyError("bad thing"), StructuredError)


def test_partial_structured_error_does_not_satisfy_protocol():
    class PartialError(Exception):
        @property
        def error_code(self) -> str:
            return "PARTIAL_001"
        # missing context property

    assert not isinstance(PartialError("partial"), StructuredError)


def test_plain_exception_does_not_satisfy_protocol():
    assert not isinstance(ValueError("plain"), StructuredError)
