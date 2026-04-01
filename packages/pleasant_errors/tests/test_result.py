from pleasant_errors import Err, Ok


def test_ok_stores_value():
    assert Ok(42).value == 42
    assert Ok("text").value == "text"
    assert Ok(None).value is None


def test_err_stores_error():
    assert Err("something went wrong").error == "something went wrong"
    assert Err(404).error == 404


def test_ok_and_err_isinstance():
    assert isinstance(Ok("hello"), Ok)
    assert not isinstance(Ok("hello"), Err)
    assert isinstance(Err("fail"), Err)
    assert not isinstance(Err("fail"), Ok)
