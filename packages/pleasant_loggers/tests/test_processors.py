"""
tests.test_processors

Unit tests for each processor in the pleasant_loggers processor chain.
Uses structlog.testing.capture_logs() — no file I/O.
"""
import logging
from datetime import datetime

import pytest
import structlog
from structlog.testing import capture_logs

from pleasant_loggers._processors import (
    KeyCollisionGuard,
    JsonSerializabilityGuard,
    RESERVED_KEYS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event_dict(**kwargs):
    """Build a minimal structlog event dict."""
    return {"event": "test event", **kwargs}


# ---------------------------------------------------------------------------
# KeyCollisionGuard
# ---------------------------------------------------------------------------

class TestKeyCollisionGuard:

    def test_passes_clean_event(self):
        """Event dict with no reserved keys should pass through unchanged."""
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(batch_id=1, user="elias")
        result = guard(None, None, event_dict)
        assert result == event_dict

    def test_raises_on_timestamp_conflict(self):
        """Passing 'timestamp' as a kwarg should raise KeyError."""
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(timestamp="2026-01-01")
        with pytest.raises(KeyError, match="timestamp"):
            guard(None, None, event_dict)

    def test_raises_on_level_conflict(self):
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(level="info")
        with pytest.raises(KeyError, match="level"):
            guard(None, None, event_dict)

    def test_raises_on_logger_conflict(self):
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(logger="mylogger")
        with pytest.raises(KeyError, match="logger"):
            guard(None, None, event_dict)

    def test_raises_on_module_conflict(self):
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(module="mymodule")
        with pytest.raises(KeyError, match="module"):
            guard(None, None, event_dict)

    def test_raises_on_func_name_conflict(self):
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(func_name="myfunc")
        with pytest.raises(KeyError, match="func_name"):
            guard(None, None, event_dict)

    def test_raises_on_lineno_conflict(self):
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(lineno=42)
        with pytest.raises(KeyError, match="lineno"):
            guard(None, None, event_dict)

    def test_raises_on_exception_conflict(self):
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(exception="some error")
        with pytest.raises(KeyError, match="exception"):
            guard(None, None, event_dict)

    def test_event_key_is_not_guarded(self):
        """'event' is in RESERVED_KEYS but must NOT be guarded (it's the message itself)."""
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict()  # already has 'event'
        result = guard(None, None, event_dict)
        assert result["event"] == "test event"

    def test_error_message_names_conflicting_keys(self):
        """KeyError message should identify which keys conflicted."""
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(timestamp="bad", module="bad")
        with pytest.raises(KeyError) as exc_info:
            guard(None, None, event_dict)
        msg = str(exc_info.value)
        assert "timestamp" in msg or "module" in msg

    def test_multiple_conflicts_raises(self):
        """Multiple reserved key conflicts should still raise KeyError."""
        guard = KeyCollisionGuard()
        event_dict = _make_event_dict(level="x", lineno=1)
        with pytest.raises(KeyError):
            guard(None, None, event_dict)


# ---------------------------------------------------------------------------
# JsonSerializabilityGuard
# ---------------------------------------------------------------------------

class TestJsonSerializabilityGuard:

    def test_passes_serializable_values(self):
        """Strings, ints, floats, bools, None, lists, dicts all pass."""
        guard = JsonSerializabilityGuard()
        event_dict = _make_event_dict(
            s="hello", i=1, f=3.14, b=True, n=None,
            lst=[1, 2], dct={"a": 1}
        )
        result = guard(None, None, event_dict)
        assert result == event_dict

    def test_raises_on_datetime(self):
        """datetime objects are not JSON-serializable — should raise TypeError."""
        guard = JsonSerializabilityGuard()
        event_dict = _make_event_dict(ts=datetime(2026, 1, 1))
        with pytest.raises(TypeError, match="ts"):
            guard(None, None, event_dict)

    def test_raises_on_custom_object(self):
        """Arbitrary objects are not JSON-serializable — should raise TypeError."""
        class MyObj:
            pass

        guard = JsonSerializabilityGuard()
        event_dict = _make_event_dict(obj=MyObj())
        with pytest.raises(TypeError, match="obj"):
            guard(None, None, event_dict)

    def test_raises_on_set(self):
        """Sets are not JSON-serializable."""
        guard = JsonSerializabilityGuard()
        event_dict = _make_event_dict(s={1, 2, 3})
        with pytest.raises(TypeError):
            guard(None, None, event_dict)

    def test_error_message_names_offending_field(self):
        """TypeError message should identify the field name and its type."""
        guard = JsonSerializabilityGuard()
        event_dict = _make_event_dict(bad_field=datetime(2026, 1, 1))
        with pytest.raises(TypeError) as exc_info:
            guard(None, None, event_dict)
        msg = str(exc_info.value)
        assert "bad_field" in msg

    def test_event_string_passes(self):
        """The 'event' string itself should pass the guard."""
        guard = JsonSerializabilityGuard()
        event_dict = {"event": "something happened"}
        result = guard(None, None, event_dict)
        assert result["event"] == "something happened"

    def test_nested_non_serializable_raises(self):
        """Non-serializable value nested inside a list should raise TypeError."""
        guard = JsonSerializabilityGuard()
        event_dict = _make_event_dict(items=[1, datetime(2026, 1, 1)])
        with pytest.raises(TypeError):
            guard(None, None, event_dict)


# ---------------------------------------------------------------------------
# RESERVED_KEYS constant
# ---------------------------------------------------------------------------

class TestReservedKeys:

    def test_contains_expected_keys(self):
        expected = {"timestamp", "level", "event", "logger", "module", "func_name", "lineno", "exception"}
        assert expected == RESERVED_KEYS

    def test_is_a_frozenset_or_set(self):
        assert isinstance(RESERVED_KEYS, (set, frozenset))
