import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

from pleasant_errors.models import AppError, StructuredError
from pleasant_errors.result import Err, Ok

_default_logger = logging.getLogger("pleasant_errors")


def catch(*exception_types: type[Exception], logger: logging.Logger | None = None):
    """Decorator that catches specified exception types and returns Err(AppError).

    On success, wraps the return value in Ok() unless it is already Ok or Err.
    On a caught exception, logs and returns Err(AppError).
    Exceptions not listed propagate normally.

    Args:
        *exception_types: Exception classes to catch. At least one is required.
        logger: Logger to use. Keyword-only. Falls back to logging.getLogger("pleasant_errors").

    Example:
        @catch(ValueError, ConnectionError, logger=my_logger)
        def fetch_user(user_id: int) -> Result[User, AppError]:
            ...
    """
    if not exception_types:
        raise TypeError(
            "catch() requires at least one exception type. "
            "Use @catch(Exception) to catch all exceptions."
        )

    _logger = logger or _default_logger

    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Ok | Err:
                try:
                    result = await func(*args, **kwargs)
                    if isinstance(result, (Ok, Err)):
                        return result
                    return Ok(result)
                except exception_types as e:
                    _logger.error(
                        f"[pleasant_errors] {type(e).__name__} in {func.__name__}: {e}"
                    )
                    # TODO: rework logging once pleasant_loggers is updated to support structured fields
                    code = e.error_code if isinstance(e, StructuredError) else type(e).__name__.upper()
                    context = e.context if isinstance(e, StructuredError) else {}
                    return Err(AppError(message=str(e), code=code, context=context))
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Ok | Err:
                try:
                    result = func(*args, **kwargs)
                    if isinstance(result, (Ok, Err)):
                        return result
                    return Ok(result)
                except exception_types as e:
                    _logger.error(
                        f"[pleasant_errors] {type(e).__name__} in {func.__name__}: {e}"
                    )
                    # TODO: rework logging once pleasant_loggers is updated to support structured fields
                    code = e.error_code if isinstance(e, StructuredError) else type(e).__name__.upper()
                    context = e.context if isinstance(e, StructuredError) else {}
                    return Err(AppError(message=str(e), code=code, context=context))
            return sync_wrapper

    return decorator
