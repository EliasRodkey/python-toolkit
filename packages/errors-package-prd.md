# PRD: `errors` Package — python-toolkit monorepo

**Author:** Elias Rodkey  
**Status:** Draft v1.0  
**Target package path:** `packages/errors`

---

## 1. Problem Statement

Across packages in the python-toolkit monorepo (`local_db`, and future packages), error handling is handled inconsistently:

- Exceptions carry only string messages, losing structured context (table names, query strings, error codes, etc.)
- try/except blocks are repeated at every call site, creating noise and inconsistency
- Failures are not visible in function signatures — callers have no indication a function can fail without reading its implementation
- Log output at error sites is freeform and hard to search or correlate

This package provides a shared, lightweight foundation for structured error handling across all packages in the monorepo.

---

## 2. Goals

- Make failure explicit in function signatures via a `Result` type
- Eliminate repetitive try/except boilerplate via a `@catch` decorator
- Preserve rich context from custom exceptions rather than collapsing them to strings
- Integrate cleanly with the monorepo's `loggers` package for structured log output
- Support both sync and async function signatures
- Impose minimal coupling — downstream packages are not required to inherit from any base class

## 3. Non-Goals (v1)

- Monadic chaining (`.map()`, `.and_then()`, `.unwrap_or()`) — may be added in v2
- Replacing Python's native exception system — exceptions are still used for unexpected failures
- Any UI or user-facing error formatting

---

## 4. Package Structure

```
packages/errors/
├── pyproject.toml
└── errors/
    ├── __init__.py          # public API exports
    ├── result.py            # Ok and Err classes
    ├── models.py            # AppError dataclass + StructuredError protocol
    └── catch.py             # @catch decorator (sync + async)
```

---

## 5. Public API

### 5.1 `Result` — `result.py`

A lightweight container representing either success or failure. Written from scratch, no external dependency.

```python
Ok(value)        # wraps a successful return value
Err(error)       # wraps an AppError on failure

Result[T, E]     # type alias: Ok[T] | Err[E]
```

**Key behaviors:**
- `Ok` and `Err` are plain dataclasses — no magic, no chaining methods in v1
- Both are generic: `Ok[User]`, `Err[AppError]`
- `isinstance(result, Ok)` and `isinstance(result, Err)` are the intended usage pattern

---

### 5.2 `AppError` + `StructuredError` — `models.py`

**`AppError`** is the standard error wrapper placed inside `Err(...)` by `@catch`:

```python
@dataclass
class AppError:
    message: str               # human-readable description
    code: str                  # machine-readable identifier e.g. "DB_1045"
    context: dict[str, Any]    # arbitrary structured context
```

**`StructuredError`** is a `Protocol` that any custom exception can implement to opt into rich context extraction. Implementing it is optional — exceptions that do not implement it fall back gracefully to basic extraction.

```python
@runtime_checkable
class StructuredError(Protocol):
    @property
    def error_code(self) -> str: ...

    @property
    def context(self) -> dict[str, Any]: ...
```

**Extraction behavior:**

| Exception type | `code` source | `context` source |
|---|---|---|
| Implements `StructuredError` | `e.error_code` | `e.context` |
| Plain exception | `type(e).__name__.upper()` | `{}` |

---

### 5.3 `@catch` decorator — `catch.py`

Wraps a function to automatically catch specified exception types, log them with full context via the `loggers` package, and return `Err(AppError)`.

**Sync signature:**
```python
@catch(ValueError, ConnectionError)
def fetch_user(user_id: int) -> Result[User, AppError]:
    ...
```

**Async signature (identical decorator, detects coroutine automatically):**
```python
@catch(ValueError, ConnectionError)
async def fetch_user(user_id: int) -> Result[User, AppError]:
    ...
```

**Behavior:**
- Catches only the exception types explicitly listed — does not swallow unexpected exceptions
- Always returns `Err(AppError)` on a caught exception
- Logs at `error` level via the `loggers` package, including: exception type, message, function name, and all context fields from `StructuredError` if implemented
- Uses `functools.wraps` to preserve the wrapped function's name, docstring, and signature
- Detects `async` functions via `asyncio.iscoroutinefunction` and wraps accordingly — no separate `@async_catch` decorator needed

---

## 6. Dependencies

| Dependency | Type | Reason |
|---|---|---|
| `loggers` | Internal (monorepo) | Structured log output at error sites |
| `structlog` | Transitive (via `loggers`) | Not imported directly by `errors` |

No external dependencies beyond `loggers`. The `result` library from PyPI is **not** used — `Ok`/`Err` are implemented in-house.

---

## 7. `pyproject.toml`

```toml
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "errors"
version = "1.0.0"
where = ["."]
description = "Structured error handling, Result types, and catch decorator for python-toolkit"
authors = [{name = "Elias Rodkey", email = "elias.rodkey@gmail.com"}]
license = {text = "MIT"}
dependencies = ["loggers"]
```

---

## 8. Usage Example

### Defining a custom exception in `local_db`

```python
# local_db/exceptions.py
class QueryError(Exception):
    def __init__(self, query: str, table: str, db_code: int):
        self.query = query
        self.table = table
        self.db_code = db_code
        super().__init__(f"Query failed on {table} with code {db_code}")

    @property
    def error_code(self) -> str:
        return f"DB_{self.db_code}"

    @property
    def context(self) -> dict:
        return {"table": self.table, "query": self.query, "db_code": self.db_code}
```

### Using `@catch` in a pipeline

```python
from errors import catch, Ok, Result, AppError
from local_db.exceptions import QueryError

@catch(QueryError, ValueError)
async def load_user(user_id: int) -> Result[dict, AppError]:
    if user_id <= 0:
        raise ValueError(f"Invalid user_id: {user_id}")
    user = await db.find(user_id)
    return Ok(user)

# Caller
result = await load_user(42)
if isinstance(result, Ok):
    print(result.value)
else:
    print(result.error)   # AppError with full context
```

### Log output on failure (via `loggers`)

```json
{
  "level": "error",
  "event": "caught_exception",
  "exc_type": "QueryError",
  "exc_message": "Query failed on users with code 1045",
  "func": "load_user",
  "table": "users",
  "query": "SELECT * FROM users WHERE id = 42",
  "db_code": 1045,
  "filename": "pipeline.py",
  "lineno": 14,
  "timestamp": "2026-03-26T10:00:00Z"
}
```

---

## 9. What is explicitly out of scope

- `@catch` does **not** support `reraise=True` in v1 — re-raising is always the caller's responsibility if they inspect `Err`
- No `Result.map()`, `Result.and_then()`, or other chaining — unwrap with `isinstance` checks
- No base class that downstream exceptions must inherit from
- No user-facing error formatting or HTTP error translation

---

## 10. Acceptance Criteria

- [ ] `Ok` and `Err` are importable from `errors` directly
- [ ] `AppError` and `StructuredError` are importable from `errors` directly
- [ ] `@catch` works identically on sync and async functions
- [ ] Exceptions implementing `StructuredError` produce full context in log output and `AppError.context`
- [ ] Plain exceptions (no protocol) fall back gracefully — no crash, reduced but valid log output
- [ ] Exceptions not listed in `@catch(...)` are not caught and propagate normally
- [ ] `functools.wraps` is used — wrapped function names and docstrings are preserved
- [ ] Full test coverage: happy path, structured exception, plain exception, async, unlisted exception passthrough
