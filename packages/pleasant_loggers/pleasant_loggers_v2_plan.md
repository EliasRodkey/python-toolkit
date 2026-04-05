# `pleasant_loggers` v2.0 — Rewrite Plan

---

## Guiding Principles

- stdlib `logging.getLogger(__name__)` call sites remain valid everywhere
- structlog is the processor engine; stdlib handles I/O
- `perf` lives on structlog bound loggers only; `add_performance_level()` remains available for stdlib users
- Flat JSON output; key collision raises an error
- Modes are first-class dataclass objects inheriting from an abstract base
- pandas is a lazy import — only loaded when `LogReader` is used

---

## New Package Structure

```
pleasant_loggers/
├── __init__.py
├── _modes.py           # AbstractLoggingMode, LoggingMode dataclass, 5 built-in instances
├── _processors.py      # custom structlog processors (perf, collision guard, caller info)
├── _config.py          # configure_logging() — replaces configure_logging.py
├── _handlers.py        # HandlerController — replaces handler_controller.py
├── _levels.py          # add_performance_level() — extracted from utils.py
├── _analysis.py        # LogReader class + CLI entry point
├── _utils.py           # file/directory utilities, timestamp helpers
└── py.typed
```

**Files deleted:** `configure_logging.py`, `handler_controller.py`, `json_log_parser.py`, `utils.py`

**Rationale for underscore-prefix internals:** public API is entirely controlled through `__init__.py` exports. Users never need to import from `_config.py` directly — this makes refactoring internals later non-breaking.

---

## Component-by-Component Spec

---

### `_modes.py`

Replace the `_MODE_DEFAULTS` dict and `LoggingMode` enum with a proper type hierarchy.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging

class DirectoryLayout(Enum):
    FLAT = "flat"
    DAILY = "daily"
    PER_RUN = "per_run"
    ROTATING = "rotating"

@dataclass
class AbstractLoggingMode(ABC):
    stream: bool
    stream_level: int
    file: bool
    file_level: int
    json: bool
    json_level: int
    directory_layout: DirectoryLayout

    @abstractmethod
    def validate(self) -> None:
        """Raise ValueError if the mode config is self-contradictory."""
        ...

@dataclass
class LoggingMode(AbstractLoggingMode):
    def validate(self):
        if not self.file and not self.json and not self.stream:
            raise ValueError("LoggingMode must enable at least one output handler.")

# Five built-in instances
BASIC_SINGLE_FILE = LoggingMode(
    stream=True, stream_level=logging.INFO,
    file=True, file_level=logging.DEBUG,
    json=False, json_level=logging.DEBUG,
    directory_layout=DirectoryLayout.FLAT,
)
BASIC_JSON_FILE = LoggingMode(...)
DIRECTORY_PER_RUN = LoggingMode(...)
DAILY_DIRECTORY = LoggingMode(...)
BASIC_ROTATING_HANDLER = LoggingMode(...)
```

**Extension pattern for users:**

```python
from pleasant_loggers import LoggingMode, DirectoryLayout
import logging

MY_MODE = LoggingMode(
    stream=False, stream_level=logging.WARNING,
    file=False, file_level=logging.DEBUG,
    json=True, json_level=logging.INFO,
    directory_layout=DirectoryLayout.DAILY,
)
configure_logging(mode=MY_MODE)
```

---

### `_processors.py`

Three custom structlog processors:

**1. `KeyCollisionGuard`** — raises `KeyError` if a user-supplied kwarg shadows a reserved field.

```python
RESERVED_KEYS = {"timestamp", "level", "event", "logger", "module", "func_name", "lineno", "exception"}

def key_collision_guard(logger, method, event_dict):
    conflicts = RESERVED_KEYS & set(event_dict.keys()) - {"event"}
    if conflicts:
        raise KeyError(f"Log context keys conflict with reserved fields: {conflicts}")
    return event_dict
```

**2. `CallerInformation`** — injects `module`, `func_name`, `lineno` automatically. Replaces the manual `StructuredLogger.makeRecord` override.

**3. `PerfContextManager`** — implemented as a method on a custom structlog bound logger class:

```python
from contextlib import contextmanager
import time

@contextmanager
def perf(self, event: str, **kwargs):
    start = time.perf_counter()
    try:
        yield self
        duration_ms = (time.perf_counter() - start) * 1000
        self.info(event, level="performance", duration_ms=round(duration_ms, 3),
                  status="ok", **kwargs)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        self.info(event, level="performance", duration_ms=round(duration_ms, 3),
                  status="error", error_type=type(exc).__name__, **kwargs)
        raise
```

**Processor chain order:**

```
key_collision_guard
→ structlog.stdlib.add_log_level
→ structlog.stdlib.add_logger_name
→ CallerInformation
→ structlog.processors.TimeStamper(fmt="iso")
→ structlog.processors.format_exc_info          # if exception present
→ structlog.processors.JSONRenderer()           # JSON handler
   OR
→ structlog.dev.ConsoleRenderer()               # stream handler
```

> JSON and console renderers are split via `ProcessorFormatter` — the JSON file handler and stream handler get different terminal processors. This is standard structlog practice.

---

### `_handlers.py` — `HandlerController`

Simplified significantly. Responsibilities:

- Resolve log file paths based on `DirectoryLayout`
- Create and own the stdlib handlers (JSON file, readable file, stream)
- Expose `json_file_path` for `LogReader`
- Application-scoped singleton via `_instance` class variable + `_reset()` for tests

**What's removed:**

- `add_file_handler()` / `get_handler(name)` multi-file routing — cut entirely
- `StructuredLogger` class — replaced by structlog bound logger
- `JSONFormatter` class — replaced by structlog's `ProcessorFormatter`

**Public interface after rewrite:**

```python
controller = HandlerController(mode=DIRECTORY_PER_RUN, log_directory="data/logs")
controller.json_file_path    # str path to the NDJSON file
controller.log_directory     # str path to the run directory
```

No runtime level-changing needed — filtering is handled at analysis time.

---

### `_config.py` — `configure_logging()`

Mostly the same interface. Key changes:

```python
def configure_logging(
    log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
    mode: AbstractLoggingMode = BASIC_SINGLE_FILE,
    # Fine-grained overrides still supported
    stream: bool | None = None,
    stream_level: int | None = None,
    file_level: int | None = None,
    json_level: int | None = None,
    rotating: bool | None = None,
    file: bool | None = None,
    json: bool | None = None,
) -> HandlerController:
```

**What changes internally:**

- Calls `structlog.configure(...)` with the processor chain
- Creates `ProcessorFormatter` instances — one for JSON (ends with `JSONRenderer`), one for console (ends with `ConsoleRenderer`)
- Attaches them to stdlib handlers on the root logger
- Calls `mode.validate()` before doing anything
- No longer calls `add_performance_level()` — that is now the user's explicit opt-in

**`file_format` param is removed** — formatting is now owned by structlog's processor chain, not a `LoggingFormats` enum. Users who need custom formatting will inject a processor via the flagged future `extra_processors` param.

---

### `_levels.py` — `add_performance_level()`

Extracted verbatim from `utils.py`. No functional change. Public export remains the same so stdlib users can keep using it.

```python
from pleasant_loggers import add_performance_level

add_performance_level()
logger = logging.getLogger(__name__)
logger.performance("step done", process_id="etl_1")
```

---

### `_analysis.py` — `LogReader` + CLI

**`LogReader` class:**

```python
class LogReader:
    def __init__(self, path: str):
        self.path = path
        self._df = None   # lazy — not loaded until accessed

    def load(self) -> "LogReader":
        """Parse NDJSON log file into internal DataFrame."""
        import pandas as pd   # lazy import
        ...
        return self           # chainable

    def to_df(self) -> "pd.DataFrame":
        """Return full log DataFrame."""

    def filter(
        self,
        level: str | list[str] | None = None,
        func_name: str | list[str] | None = None,
        module: str | None = None,
        start: str | None = None,   # ISO string or datetime
        end: str | None = None,
    ) -> "pd.DataFrame":
        """Single filter method covering all common axes."""

    def performance_summary(self) -> "pd.DataFrame":
        """Group PERFORMANCE records by func_name, return avg/min/max duration_ms."""

    def activity_timeline(self, func_name: str) -> "pd.DataFrame":
        """All records for a given function, sorted by timestamp."""
```

No `LogRecord` dataclass — everything is a DataFrame row. Simpler, more flexible, plays well with pandas filtering downstream.

**Format flexibility:** `LogReader` doesn't assume the nested `extra` structure — it reads any flat NDJSON. Unknown fields land as nullable columns. This satisfies the "doesn't require JSON logs to be in a certain format" requirement.

**CLI entry point:**

```
python -m pleasant_loggers.analyze <log_file> [options]

Options:
  --level PERFORMANCE ERROR     filter by one or more levels
  --func process_batch          filter by function name
  --start 2026-03-01            start datetime filter
  --end 2026-03-26              end datetime filter
  --summary                     print performance_summary() table
  --output results.csv          write filtered DataFrame to CSV
```

Registered in `pyproject.toml`:

```toml
[project.scripts]
pleasant-logs = "pleasant_loggers._analysis:cli_main"
```

---

### `__init__.py` — Public API

```python
# Configuration
from ._config import configure_logging
from ._handlers import HandlerController
from ._modes import (
    LoggingMode, AbstractLoggingMode, DirectoryLayout,
    BASIC_SINGLE_FILE, BASIC_JSON_FILE, DIRECTORY_PER_RUN,
    DAILY_DIRECTORY, BASIC_ROTATING_HANDLER,
)

# Levels
from ._levels import add_performance_level

# Analysis (pandas loaded lazily inside LogReader)
from ._analysis import LogReader

# Utilities
from ._utils import (
    get_log_directories, get_log_files,
    delete_log_directory, delete_todays_logs, clear_logs,
)

__version__ = "2.0.0"
__author__ = "Elias Rodkey"
```

**Removed from public API:**

- `StructuredLogger` — internal concern, replaced by structlog bound logger
- `JSONLogParser`, `LogRecord` — replaced by `LogReader`
- `LoggingFormats` — removed; formatting owned by structlog processor chain
- `create_datestamp`, `create_timestamp`, `create_log_datetime_stamp`, `compose_global_run_id` — moved to `_utils.py` as private helpers; re-expose only if external usage is confirmed

---

## JSON Output Format (v2)

Every record is a flat NDJSON line (one JSON object per line).

**Standard record:**

```json
{
  "timestamp": "2026-03-26T14:32:01.123456Z",
  "level": "info",
  "event": "Processing batch",
  "logger": "pleasant_database.database_manager",
  "func_name": "run_batch",
  "module": "database_manager",
  "lineno": 84,
  "batch_id": 123,
  "user": "elias",
  "exception": null
}
```

**PERFORMANCE record:**

```json
{
  "timestamp": "2026-03-26T14:32:01.267Z",
  "level": "performance",
  "event": "run_batch",
  "logger": "pleasant_database.database_manager",
  "func_name": "run_batch",
  "module": "database_manager",
  "lineno": 84,
  "duration_ms": 142.3,
  "status": "ok",
  "batch_id": 123
}
```

**PERFORMANCE record (on exception):**

```json
{
  "timestamp": "2026-03-26T14:32:01.267Z",
  "level": "performance",
  "event": "run_batch",
  "duration_ms": 38.1,
  "status": "error",
  "error_type": "ValueError",
  "batch_id": 123
}
```

---

## `pyproject.toml` Changes

```toml
[project]
name = "pleasant-loggers"
version = "2.0.0"

dependencies = [
    "structlog>=24.0",
]

# pandas is NOT in base deps — imported lazily in LogReader
# To make it explicit in future:
# [project.optional-dependencies]
# analysis = ["pandas>=2.0"]

[project.scripts]
pleasant-logs = "pleasant_loggers._analysis:cli_main"
```

---

## Migration Notes for `pleasant_database`

`pleasant_database/__init__.py` currently calls `configure_logging()` at import time — that stays unchanged.

**Two call sites need updating:**

**1. Performance level registration**

`configure_logging()` no longer calls `add_performance_level()` automatically. Add it explicitly in `pleasant_database/__init__.py`:

```python
from pleasant_loggers import configure_logging, add_performance_level

handler_controller = configure_logging(log_directory=LOG_DIRECTORY)
add_performance_level()
```

**2. `LoggingExtras` extra dict pattern**

The `extra={LoggingExtras.FILE: path}` pattern used in `database_file.py` and similar modules goes away with flat kwargs. Modules that switch to structlog bound loggers update call sites to:

```python
logger.info("Creating database file", file=self.name)
```

Modules that keep `logging.getLogger()` can retain `extra={}` dict syntax — structlog's stdlib integration passes unknown extra fields through the processor chain and flattens them in the JSON output. No forced migration required.

---

## Flagged for Future Consideration

| Feature | Notes |
|---|---|
| Custom processor injection | `extra_processors` param in `configure_logging()` — lets users add context fields like `service_name` or `env` without forking the package |
| Log record sampling | `sample_rate` processor for high-throughput scenarios where logging every DEBUG record is expensive |
| Redaction processor | Auto-redact fields matching patterns like `password`, `token`, `secret` before they reach the JSON file; user-extensible redaction list |

---

## Version & Release

This is a **breaking change**. Release as `2.0.0`.

- Tag `v2.0.0` in the monorepo after both packages are updated
- Update `pleasant_database` to pin `pleasant-loggers>=2.0` and publish in the same release
- Update README to reflect new public API and call site patterns
