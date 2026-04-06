"""
pleasant_loggers._loggers

get_logger() — the entry point for structlog-backed loggers with perf() and
timed() performance timing methods.

Usage:
    from pleasant_loggers import get_logger

    logger = get_logger(__name__)

    # Context manager — time a block of code
    with logger.perf("run_batch", batch_id=123):
        do_work()

    # Decorator — time an entire function, capturing its args automatically
    @logger.timed("process_item")
    def process_item(self, item_id, table_name):
        ...
"""
import functools
import inspect
import logging
import time
import warnings
from contextlib import contextmanager
from typing import Any

import structlog
import structlog.stdlib

from pleasant_loggers._handlers import HandlerController
from pleasant_loggers._levels import PERFORMANCE_LEVEL_NUM

# Register PERFORMANCE level with structlog's internal level-to-name mapping
# so that BoundLogger.log(15, ...) resolves to "performance".
# Also ensure the stdlib Logger has the method needed by the structlog proxy.
if PERFORMANCE_LEVEL_NUM not in structlog.stdlib.LEVEL_TO_NAME:
    structlog.stdlib.LEVEL_TO_NAME[PERFORMANCE_LEVEL_NUM] = "performance"
    logging.addLevelName(PERFORMANCE_LEVEL_NUM, "PERFORMANCE")

    def _performance_method(self, message, *args, **kwargs):
        if self.isEnabledFor(PERFORMANCE_LEVEL_NUM):
            stacklevel = kwargs.pop("stacklevel", 1)
            self._log(PERFORMANCE_LEVEL_NUM, message, args, stacklevel=stacklevel + 1, **kwargs)

    if not hasattr(logging.Logger, "performance"):
        logging.Logger.performance = _performance_method


class _BoundLoggerWithPerf(structlog.stdlib.BoundLogger):
    """
    Structlog BoundLogger subclass that adds perf() and timed() methods.
    """

    @contextmanager
    def perf(self, event: str, **kwargs):
        """
        Context manager that times a block of code and emits a PERFORMANCE log
        record with duration_ms, status, and optional error_type.

        Args:
            event: Name of the operation being timed.
            **kwargs: Additional fields to include in the log record.
        """
        start = time.perf_counter()
        try:
            yield self
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            self.log(
                PERFORMANCE_LEVEL_NUM,
                event,
                duration_ms=duration_ms,
                status="ok",
                **kwargs,
            )
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            self.log(
                PERFORMANCE_LEVEL_NUM,
                event,
                duration_ms=duration_ms,
                status="error",
                error_type=type(exc).__name__,
                **kwargs,
            )
            raise

    def timed(self, event: str):
        """
        Decorator that times a function and emits a PERFORMANCE log record.

        Automatically captures the decorated function's call-time arguments
        (excluding 'self' and 'cls') as log record fields.

        Args:
            event: Name of the operation (used as the log event name).
        """
        def decorator(fn):
            sig = inspect.signature(fn)

            @functools.wraps(fn)
            def wrapper(*args, **call_kwargs):
                # Bind call-time arguments and filter out self/cls
                try:
                    bound = sig.bind(*args, **call_kwargs)
                    bound.apply_defaults()
                    captured = {
                        k: v for k, v in bound.arguments.items()
                        if k not in ("self", "cls")
                    }
                except TypeError:
                    captured = {}

                start = time.perf_counter()
                try:
                    result = fn(*args, **call_kwargs)
                    duration_ms = round((time.perf_counter() - start) * 1000, 3)
                    self.log(
                        PERFORMANCE_LEVEL_NUM,
                        event,
                        duration_ms=duration_ms,
                        status="ok",
                        **captured,
                    )
                    return result
                except Exception as exc:
                    duration_ms = round((time.perf_counter() - start) * 1000, 3)
                    self.log(
                        PERFORMANCE_LEVEL_NUM,
                        event,
                        duration_ms=duration_ms,
                        status="error",
                        error_type=type(exc).__name__,
                        **captured,
                    )
                    raise

            return wrapper
        return decorator


def get_logger(name: str) -> _BoundLoggerWithPerf:
    """
    Return a structlog bound logger with perf() and timed() timing methods.

    If called before configure_logging(), emits a UserWarning with setup
    instructions and falls back to structlog defaults.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A structlog bound logger instance with perf() and timed() available.
    """
    if not HandlerController._initialized:
        warnings.warn(
            f"get_logger({name!r}) was called before configure_logging(). "
            "Logger will use structlog defaults. "
            "Call configure_logging() at application startup before get_logger().",
            UserWarning,
            stacklevel=2,
        )

    return structlog.get_logger(name, wrapper_class=_BoundLoggerWithPerf)
