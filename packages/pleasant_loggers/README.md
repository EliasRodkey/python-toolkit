# Loggers

A flexible, modular logging package for Python that integrates cleanly with the native `logging` library. Supports structured JSON logging, named logging profiles, and automatic log file organization.

## Description

Loggers provides a standardized way to configure and manage log output across a Python project. It adds structured JSON logging, a custom PERFORMANCE log level, and named profiles (modes) for different environments.

## Main Components

- **`configure_logging()`** — Configures the root logger with file, JSON, and optional stream handlers. Returns a `HandlerController`.
- **`HandlerController`** — Singleton-like class that manages all handlers for a run. Ensures all loggers write to the same files.
- **`LoggingMode`** — Enum that selects a logging profile. Five built-in modes; see below.
- **`JSONLogParser`** — Reads, filters, and interprets a JSON log file produced by the package.
- **`Logger`** — **Deprecated.** Do not use.

---

## Usage

### Basic setup

```python
import logging
from pleasant_loggers import configure_logging

log_controller = configure_logging()
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning!")
logger.performance("Timing measurement", process_id="step_1")
```

By default this uses `LoggingMode.BASIC_SINGLE_FILE`, which writes a readable `.log` file directly into `data/logs/` and adds a console stream handler at INFO level.

---

### Logging modes

Pass a `LoggingMode` to select the environment profile:

```python
from pleasant_loggers import configure_logging, LoggingMode

# Single readable log file in flat directory, INFO to console (default)
configure_logging(mode=LoggingMode.BASIC_SINGLE_FILE)

# Single JSON log file in flat directory, INFO to console
configure_logging(mode=LoggingMode.BASIC_JSON_FILE)

# Per-run timestamped folder, readable + JSON files, INFO to console
configure_logging(mode=LoggingMode.DIRECTORY_PER_RUN)

# Daily folder, readable + JSON files, no console output
configure_logging(mode=LoggingMode.DAILY_DIRECTORY)

# Flat directory, TimedRotatingFileHandler (rotates at midnight, keeps 30 days),
# readable + JSON files, WARNING+ to console
configure_logging(mode=LoggingMode.BASIC_ROTATING_HANDLER)
```

**Mode defaults summary:**

Mode                    | Directory layout                          | Text file | JSON file | Stream level
----------------------- | ----------------------------------------- | --------- | --------- | ------------
`BASIC_SINGLE_FILE`     | `data/logs/` (flat)                       | ✓         | —         | INFO
`BASIC_JSON_FILE`       | `data/logs/` (flat)                       | —         | ✓         | INFO
`DIRECTORY_PER_RUN`     | `data/logs/YYYY-MM-DD/YYYY-MM-DD_HHMMSS/` | ✓         | ✓         | INFO
`DAILY_DIRECTORY`       | `data/logs/YYYY-MM-DD/`                   | ✓         | ✓         | *(none)*
`BASIC_ROTATING_HANDLER`| `data/logs/` (flat, rotating)             | ✓         | ✓         | WARNING

---

### Keyword overrides

Any mode default can be overridden with explicit keyword arguments:

```python
configure_logging(
    log_directory="my/custom/logs",   # default: "data/logs"
    mode=LoggingMode.BASIC_ROTATING_HANDLER,
    stream=False,                     # suppress console output
    stream_level=logging.ERROR,       # override console level
    file_level=logging.INFO,          # override text file level
    json_level=logging.WARNING,       # override JSON file level
    file_format=LoggingFormats.FORMAT_FUNC_NAME,  # override text format
    rotating=True,                    # use TimedRotatingFileHandler
    file=False,                       # omit the text file handler
    json=False,                       # omit the JSON file handler
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
from pleasant_loggers import JSONLogParser

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
from pleasant_loggers import get_log_directories, get_log_files, delete_todays_logs, clear_logs

get_log_directories()        # list of entries in data/logs/
get_log_files()              # dict: directory -> list of log file names
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
- 1.5: Rename modes to BASIC_SINGLE_FILE, BASIC_JSON_FILE, DIRECTORY_PER_RUN, DAILY_DIRECTORY, BASIC_ROTATING_HANDLER; add `file`, `json`, `json_level`, `file_format`, `rotating` overrides to `configure_logging`; default mode changed to BASIC_SINGLE_FILE

## License

This project is licensed under the MIT License — see the LICENSE file for details.
