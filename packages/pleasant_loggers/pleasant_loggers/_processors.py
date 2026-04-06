"""
pleasant_loggers._processors

Custom structlog processors and the shared processor chain used by
configure_logging().

Processors:
    KeyCollisionGuard   — raises KeyError if a user kwarg shadows a reserved field
    JsonSerializabilityGuard — raises TypeError if a value is not JSON-serializable

Processor chain order (shared):
    ExtraAdder
    → KeyCollisionGuard
    → JsonSerializabilityGuard
    → add_log_level
    → add_logger_name
    → CallsiteParameterAdder(MODULE, FUNC_NAME, LINENO)
    → TimeStamper(fmt="iso")
    → format_exc_info
    → [JSONRenderer | ConsoleRenderer]   # per handler, set in _config.py
"""
import json

import structlog
from structlog.processors import CallsiteParameter, CallsiteParameterAdder


RESERVED_KEYS: frozenset = frozenset({
    "timestamp", "level", "event", "logger",
    "module", "func_name", "lineno", "exception",
})


class KeyCollisionGuard:
    """
    Raises KeyError if any key in the event dict (other than 'event' itself)
    conflicts with a reserved output field.

    Must run before structlog's own processors inject reserved keys.
    """

    def __call__(self, logger, method, event_dict: dict) -> dict:
        conflicts = (set(event_dict.keys()) - {"event"}) & RESERVED_KEYS
        if conflicts:
            raise KeyError(
                f"Log context keys conflict with reserved fields: {sorted(conflicts)}"
            )
        return event_dict


class JsonSerializabilityGuard:
    """
    Raises TypeError if any value in the event dict is not JSON-serializable.

    Runs early (after KeyCollisionGuard), before structlog adds its own fields,
    so only user-supplied values are validated at this point.
    """

    def __call__(self, logger, method, event_dict: dict) -> dict:
        for key, value in event_dict.items():
            # Skip structlog internal keys (prefixed with '_')
            if isinstance(key, str) and key.startswith("_"):
                continue
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                raise TypeError(
                    f"Log field '{key}' contains a non-JSON-serializable value "
                    f"of type {type(value).__name__!r}. "
                    f"Convert it to a JSON-safe type before logging."
                )
        return event_dict


def build_shared_processor_chain() -> list:
    """
    Returns the shared processor list used by structlog.configure().

    The terminal renderer (JSONRenderer or ConsoleRenderer) is NOT included here —
    it is attached per-handler via ProcessorFormatter in _config.py.
    """
    return [
        structlog.stdlib.ExtraAdder(),
        KeyCollisionGuard(),
        JsonSerializabilityGuard(),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        CallsiteParameterAdder(
            [
                CallsiteParameter.MODULE,
                CallsiteParameter.FUNC_NAME,
                CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.format_exc_info,
    ]
