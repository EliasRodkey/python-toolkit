import asyncio
import logging
import pytest
from pleasant_errors import Error, Err, Ok, catch


# --- Helpers ---

class StructuredExc(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)

    @property
    def error_code(self) -> str:
        return "STRUCTURED_001"

    @property
    def context(self) -> dict:
        return {"detail": "some detail"}


# --- Sync: happy path ---

def test_sync_plain_return_wrapped_in_ok():
    @catch(ValueError)
    def fn():
        return 42

    result = fn()
    assert isinstance(result, Ok)
    assert result.value == 42


def test_sync_explicit_ok_passed_through():
    @catch(ValueError)
    def fn():
        return Ok("already wrapped")

    result = fn()
    assert isinstance(result, Ok)
    assert result.value == "already wrapped"


def test_sync_explicit_err_passed_through():
    @catch(ValueError)
    def fn():
        return Err(Error(message="manual", code="MANUAL_ERR"))

    result = fn()
    assert isinstance(result, Err)
    assert result.error.code == "MANUAL_ERR"


# --- Sync: caught exception ---

def test_sync_plain_exception_returns_err():
    @catch(ValueError)
    def fn():
        raise ValueError("bad input")

    result = fn()
    assert isinstance(result, Err)
    assert isinstance(result.error, Error)
    assert result.error.message == "bad input"
    assert result.error.code == "VALUEERROR"
    assert result.error.context == {}


def test_sync_structured_exception_extracts_code_and_context():
    @catch(StructuredExc)
    def fn():
        raise StructuredExc("structured failure")

    result = fn()
    assert isinstance(result, Err)
    assert result.error.code == "STRUCTURED_001"
    assert result.error.context == {"detail": "some detail"}
    assert result.error.message == "structured failure"


# --- Sync: unlisted exception propagates ---

def test_sync_unlisted_exception_propagates():
    @catch(ValueError)
    def fn():
        raise RuntimeError("unexpected")

    with pytest.raises(RuntimeError, match="unexpected"):
        fn()


# --- Sync: functools.wraps ---

def test_sync_wraps_preserves_name_and_docstring():
    @catch(ValueError)
    def my_function():
        """My docstring."""
        return 1

    assert my_function.__name__ == "my_function"
    assert my_function.__doc__ == "My docstring."


# --- Async: happy path ---

def test_async_plain_return_wrapped_in_ok():
    @catch(ValueError)
    async def fn():
        return 99

    result = asyncio.run(fn())
    assert isinstance(result, Ok)
    assert result.value == 99


def test_async_explicit_ok_passed_through():
    @catch(ValueError)
    async def fn():
        return Ok("async wrapped")

    result = asyncio.run(fn())
    assert isinstance(result, Ok)
    assert result.value == "async wrapped"


def test_async_explicit_err_passed_through():
    @catch(ValueError)
    async def fn():
        return Err(Error(message="async manual", code="ASYNC_ERR"))

    result = asyncio.run(fn())
    assert isinstance(result, Err)
    assert result.error.code == "ASYNC_ERR"


# --- Async: caught exception ---

def test_async_plain_exception_returns_err():
    @catch(ValueError)
    async def fn():
        raise ValueError("async bad input")

    result = asyncio.run(fn())
    assert isinstance(result, Err)
    assert result.error.message == "async bad input"
    assert result.error.code == "VALUEERROR"
    assert result.error.context == {}


def test_async_structured_exception_extracts_code_and_context():
    @catch(StructuredExc)
    async def fn():
        raise StructuredExc("async structured")

    result = asyncio.run(fn())
    assert isinstance(result, Err)
    assert result.error.code == "STRUCTURED_001"
    assert result.error.context == {"detail": "some detail"}


# --- Async: unlisted exception propagates ---

def test_async_unlisted_exception_propagates():
    @catch(ValueError)
    async def fn():
        raise RuntimeError("async unexpected")

    with pytest.raises(RuntimeError, match="async unexpected"):
        asyncio.run(fn())


# --- Async: functools.wraps ---

def test_async_wraps_preserves_name_and_docstring():
    @catch(ValueError)
    async def my_async_function():
        """Async docstring."""
        return 1

    assert my_async_function.__name__ == "my_async_function"
    assert my_async_function.__doc__ == "Async docstring."


# --- Decorator validation ---

def test_no_exception_types_raises_type_error():
    with pytest.raises(TypeError):
        @catch()
        def fn():
            return 1


# --- None return ---

def test_sync_none_return_wrapped_in_ok():
    @catch(ValueError)
    def fn():
        return None

    result = fn()
    assert isinstance(result, Ok)
    assert result.value is None


# --- Multiple exception types ---

def test_catch_multiple_exception_types():
    @catch(ValueError, TypeError)
    def fn(exc):
        raise exc

    result_value = fn(ValueError("value err"))
    assert isinstance(result_value, Err)
    assert result_value.error.code == "VALUEERROR"

    result_type = fn(TypeError("type err"))
    assert isinstance(result_type, Err)
    assert result_type.error.code == "TYPEERROR"


# --- Logger parameter ---

def test_default_logger_logs_on_exception(caplog):
    @catch(ValueError)
    def fn():
        raise ValueError("default logger error")

    with caplog.at_level(logging.ERROR, logger="pleasant_errors"):
        result = fn()

    assert isinstance(result, Err)
    assert "default logger error" in caplog.text


def test_custom_logger_is_called_on_exception(caplog):
    custom_logger = logging.getLogger("test_custom")

    @catch(ValueError, logger=custom_logger)
    def fn():
        raise ValueError("logged error")

    with caplog.at_level(logging.ERROR, logger="test_custom"):
        result = fn()

    assert isinstance(result, Err)
    assert "logged error" in caplog.text
