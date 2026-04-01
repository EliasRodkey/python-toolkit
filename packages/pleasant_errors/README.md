# pleasant_errors

A lightweight error-handling package for Python that brings Rust-style `Result` types and a decorator-based exception catcher to your codebase.

## Description

`pleasant_errors` provides a clean, explicit alternative to try/except blocks scattered throughout your code. Functions return `Ok` or `Err` instead of raising, making error paths visible in type signatures and easy to handle at the call site.

## Main Components

- **`Ok` / `Err`** — Generic dataclasses wrapping a success value or an error value.
- **`Result[T, E]`** — Type alias for `Ok[T] | Err[E]`. Use in annotations to signal a function may fail.
- **`Error`** — Dataclass for structured error payloads: `message`, `code`, and optional `context` dict.
- **`StructuredError`** — Protocol for custom exception classes that carry `error_code` and `context`. Detected automatically by `catch`.
- **`catch`** — Decorator that catches specified exception types and returns `Err(Error)` instead of raising. Supports both sync and async functions.

---

## Usage

### Result type

```python
from pleasant_errors import Ok, Err, Result, Error

def divide(a: float, b: float) -> Result[float, Error]:
    if b == 0:
        return Err(Error(message="Division by zero", code="DIVISION_BY_ZERO"))
    return Ok(a / b)

result = divide(10, 2)

if isinstance(result, Ok):
    print(result.value)   # 5.0
else:
    print(result.error)   # Error(message=..., code=...)
```

---

### `@catch` decorator

Wrap a function with `@catch` to convert exceptions into `Err` values automatically. At least one exception type is required.

```python
from pleasant_errors import catch, Ok, Err, Result, Error

@catch(ValueError, KeyError)
def parse_config(raw: dict) -> Result[str, Error]:
    return raw["setting"].strip()

result = parse_config({})   # KeyError caught → Err(Error(...))
result = parse_config({"setting": "prod"})  # → Ok("prod")
```

If the decorated function already returns `Ok` or `Err`, the wrapper passes it through unchanged. Any exception type *not* listed in `@catch` propagates normally.

---

### Async support

`@catch` works identically on async functions:

```python
@catch(ConnectionError, TimeoutError)
async def fetch_data(url: str) -> Result[bytes, Error]:
    ...
```

---

### Custom logger

Pass a `logger` keyword argument to route error logs to a specific logger:

```python
import logging
from pleasant_errors import catch

my_logger = logging.getLogger("my_app")

@catch(Exception, logger=my_logger)
def risky_operation() -> ...:
    ...
```

Without a logger, errors are logged to `logging.getLogger("pleasant_errors")`.

---

### `StructuredError` protocol

If your custom exceptions implement `error_code` and `context` properties, `catch` will use them when building the `Err` payload:

```python
from pleasant_errors import StructuredError

class DatabaseError(Exception):
    @property
    def error_code(self) -> str:
        return "DB_ERROR"

    @property
    def context(self) -> dict:
        return {"table": "users"}
```

For plain exceptions, `code` defaults to the exception class name in uppercase (e.g. `"VALUEERROR"`).

---

## Version History

- 1.0.0: Initial creation.

## License

This project is licensed under the MIT License — see the LICENSE file for details.
