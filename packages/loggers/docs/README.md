# Loggers

A flexible, modular logging package for Python that integrates cleanly with the native `logging` library. Supports structured JSON logging, named logging profiles, and automatic log file organization.

## Description

Loggers provides a standardized way to configure and manage log output across a Python project. It adds structured JSON logging, a custom PERFORMANCE log level, and named profiles (modes) for different environments.

## Main Components

- **`configure_logging()`** — Configures the root logger with file, JSON, and optional stream handlers. Returns a `HandlerController`.
- **`HandlerController`** — Singleton-like class that manages all handlers for a run. Ensures all loggers write to the same files.
- **`LoggingMode`** — Enum that selects a logging profile (DEVELOPMENT, TEST, PRODUCTION).
- **`JSONLogParser`** — Reads, filters, and interprets a JSON log file produced by the package.
- **`Logger`** — **Deprecated.** Do not use.

---

## Usage

### Basic setup

```python
import logging
from loggers import configure_logging

log_controller = configure_logging()
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning!")
logger.performance("Timing measurement", process_id="step_1")
```

By default this creates `data/logs/YYYY-MM-DD/YYYY-MM-DD_HHMMSS/` with a readable `.log` file, a structured `.json.log` file, and a console stream handler at INFO level.

---

### Logging modes

Pass a `LoggingMode` to select the environment profile:

```python
from loggers import configure_logging, LoggingMode

# Development (default): folder-per-run, DEBUG to files, INFO to console
configure_logging(mode=LoggingMode.DEVELOPMENT)

# Test: daily folder only, DEBUG to files, no console output
configure_logging(mode=LoggingMode.TEST)

# Production: TimedRotatingFileHandler (rotates at midnight, keeps 30 days),
#             DEBUG to files, WARNING+ to console
configure_logging(mode=LoggingMode.PRODUCTION)
```

**Log directory layout by mode:**

Mode        | Layout
----------- | ----------------------------------------------
DEVELOPMENT | `data/logs/YYYY-MM-DD/YYYY-MM-DD_HHMMSS/`
TEST        | `data/logs/YYYY-MM-DD/`
PRODUCTION  | `data/logs/loggers.json.log` (rotating)

---

### Keyword overrides

Any mode default can be overridden with explicit keyword arguments:

```python
configure_logging(
    log_directory="my/custom/logs",
    mode=LoggingMode.PRODUCTION,
    stream=False,             # suppress console output
    stream_level=logging.ERROR,
    file_level=logging.INFO,
)
```

---

### Custom PERFORMANCE level

A `performance` method is added to all loggers. Use it to record timing or throughput metrics. The optional `process_id` kwarg attaches an identifier to the extra dict for filtering later.

```python
logger.performance("Batch processed", process_id="etl_step_2")
```

---

### Multiple file handlers

Add additional named file handlers to route specific loggers to separate files within the same run directory:

```python
log_controller.add_file_handler("worker_thread")

worker_logger = logging.getLogger("worker")
worker_logger.addHandler(log_controller.get_handler("worker_thread"))
```

---

### JSONLogParser

Parse and filter the structured JSON log file produced by each run:

```python
from loggers import JSONLogParser

parser = JSONLogParser(log_controller.json_file_path)
parser.load()

# Filter methods — each returns a list of LogRecord dataclass objects
parser.filter_by_level("ERROR", "CRITICAL")
parser.filter_by_time(start_date=datetime(...), end_date=datetime(...))
parser.filter_by_extra("process_id")
parser.get_records_by_id([record_ids])
parser.top_messages(n=10)

# Metrics (populated after load())
parser.level_counts    # dict: level -> count
parser.func_counts     # dict: function name -> count
parser.module_counts   # dict: module name -> count

# Convert to pandas DataFrame
parser.to_dataframe(records)  # pass a filtered list, or None for all records
```

---

### Log file utilities

```python
from loggers import get_log_directories, get_log_files, delete_todays_logs, clear_logs

get_log_directories()        # list of date folders in data/logs/
get_log_files()              # dict: date folder -> list of log file names
delete_todays_logs()         # delete today's log directory
clear_logs()                 # delete all log directories
```

---

## Version History

- 1.0: Initial release
- 1.1: Deprecate `Logger` class; replace with native logging helpers
- 1.2: Add `configure_logging`, JSON log generation, and `JSONLogParser`
- 1.3: Rewrite `HandlerController` and `configure_logging` tests; add `_reset()` for test isolation; add PERFORMANCE log level
- 1.4: Add `LoggingMode` enum (DEVELOPMENT / TEST / PRODUCTION); add `TimedRotatingFileHandler` support for PRODUCTION mode; `configure_logging` keyword overrides for stream, stream_level, file_level

## License

This project is licensed under the MIT License — see the LICENSE file for details.
