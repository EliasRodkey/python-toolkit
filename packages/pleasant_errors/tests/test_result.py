import pytest
from pleasant_errors import Err, Ok


def test_ok_stores_value():
    result = Ok(42)
    assert result.value == 42


def test_err_stores_error():
    result = Err("something went wrong")
    assert result.error == "something went wrong"


def test_ok_isinstance():
    assert isinstance(Ok("hello"), Ok)
    assert not isinstance(Ok("hello"), Err)


def test_err_isinstance():
    assert isinstance(Err("fail"), Err)
    assert not isinstance(Err("fail"), Ok)


def test_ok_is_generic():
    ok_int = Ok(1)
    ok_str = Ok("text")
    assert ok_int.value == 1
    assert ok_str.value == "text"


def test_err_is_generic():
    err_str = Err("error")
    err_int = Err(404)
    assert err_str.error == "error"
    assert err_int.error == 404
