from pleasant_errors import AppError, StructuredError


def test_app_error_fields():
    err = AppError(message="something failed", code="DB_1045", context={"table": "users"})
    assert err.message == "something failed"
    assert err.code == "DB_1045"
    assert err.context == {"table": "users"}


def test_app_error_default_context():
    err = AppError(message="oops", code="VALUEERROR")
    assert err.context == {}


def test_structured_error_protocol_satisfied():
    class MyError(Exception):
        @property
        def error_code(self) -> str:
            return "MY_001"

        @property
        def context(self) -> dict:
            return {"key": "value"}

    e = MyError("bad thing")
    assert isinstance(e, StructuredError)


def test_plain_exception_does_not_satisfy_protocol():
    e = ValueError("plain")
    assert not isinstance(e, StructuredError)
