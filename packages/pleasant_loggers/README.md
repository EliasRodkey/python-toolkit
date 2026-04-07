# pleasant_loggers

A structured logging package for Python built on [structlog](https://www.structlog.org/). Produces flat NDJSON output, supports automatic performance timing, and includes a pandas-backed log reader and CLI.

## Installation

```bash
pip install pleasant-loggers

# With log analysis support (pandas required for LogReader):
pip install pleasant-loggers[analysis]
```

## Description

`pleasant_loggers` configures Python's stdlib `logging` with structlog as the processor engine. All log output is flat NDJSON — no nested `extra` dicts, no custom formatters to maintain. The package adds two timing primitives (`perf()` context manager and `timed()` decorator) and a `LogReader` class for programmatic log analysis.

---

## Quick start

```python
import logging
from pleasant_loggers import configure_logging, add_performance_level, get_logger

# Configure once at application startup
log_controller = configure_logging()

# Optional: register the PERFORMANCE log level for stdlib loggers
add_performance_level()

# Stdlib logger — works exactly as before
stdlib_logger = logging.getLogger(__name__)
stdlib_logger.info("Starting up")

# Structlog-backed logger — flat kwargs, plus perf() and timed()
logger = get_logger(__name__)
logger.info("Processing item", item_id=42, table="orders")
```

---

## Logging modes

Pass a built-in mode or construct your own `LoggingMode`:

```python
from pleasant_loggers import configure_logging, DIRECTORY_PER_RUN, DAILY_DIRECTORY, BASIC_ROTATING_HANDLER

configure_logging(mode=DIRECTORY_PER_RUN)
```

**Built-in modes:**

| Mode | Directory layout | Text file | JSON file | Stream level |
|---|---|---|---|---|
| `BASIC_SINGLE_FILE` | `data/logs/` (flat) | ✓ | — | INFO |
| `BASIC_JSON_FILE` | `data/logs/` (flat) | — | ✓ | INFO |
| `DIRECTORY_PER_RUN` | `data/logs/YYYY-MM-DD/YYYY-MM-DD_HHMMSS/` | ✓ | ✓ | INFO |
| `DAILY_DIRECTORY` | `data/logs/YYYY-MM-DD/` | ✓ | ✓ | *(none)* |
| `BASIC_ROTATING_HANDLER` | `data/logs/` (flat, rotating) | ✓ | ✓ | WARNING |

### Fine-grained overrides

Any field on the mode can be overridden without constructing a new `LoggingMode`:

```python
configure_logging(
    log_directory="my/custom/logs",
    mode=DIRECTORY_PER_RUN,
    stream=False,
    stream_level=logging.ERROR,
    file_level=logging.INFO,
    json_level=logging.WARNING,
    file=False,
    json=True,
)
```

Overrides are applied via `dataclasses.replace()` — the built-in mode instances are never mutated.

### Custom modes

Subclass `AbstractLoggingMode` or construct a `LoggingMode` directly:

```python
from pleasant_loggers import LoggingMode, DirectoryLayout, configure_logging
import logging

MY_MODE = LoggingMode(
    stream=False,
    stream_level=logging.WARNING,
    file=False,
    file_level=logging.DEBUG,
    json=True,
    json_level=logging.INFO,
    directory_layout=DirectoryLayout.DAILY,
)
configure_logging(mode=MY_MODE)
```

---

## JSON output format

Every record is a flat NDJSON line. No nested `extra` key.

```json
{
  "timestamp": "2026-03-26T14:32:01.123456Z",
  "level": "info",
  "event": "Processing batch",
  "logger": "my_app.database",
  "func_name": "run_batch",
  "module": "database",
  "lineno": 84,
  "batch_id": 123,
  "user": "elias"
}
```

PERFORMANCE records include `duration_ms`, `status`, and (on error) `error_type`:

```json
{
  "timestamp": "2026-03-26T14:32:01.267Z",
  "level": "performance",
  "event": "run_batch",
  "func_name": "run_batch",
  "module": "database",
  "lineno": 84,
  "duration_ms": 142.3,
  "status": "ok",
  "batch_id": 123
}
```

---

## Structlog-backed logger

Use `get_logger()` for flat-kwargs logging and performance timing:

```python
from pleasant_loggers import get_logger

logger = get_logger(__name__)

# Flat kwargs — appear as top-level fields in JSON output
logger.info("Item saved", table="orders", item_id=99)
logger.error("Query failed", query="SELECT *", error_code=500)
```

### `perf()` — context manager

Times a block of code and emits a PERFORMANCE record automatically:

```python
with logger.perf("run_batch", batch_id=123):
    process_data()

# On success:  status="ok",   duration_ms=142.3
# On exception: status="error", error_type="ValueError", duration_ms=38.1
# Exceptions are re-raised after the record is emitted.
```

### `timed()` — decorator

Times an entire function and captures its call-time arguments automatically:

```python
@logger.timed("process_item")
def process_item(item_id, table_name):
    ...

# Emits PERFORMANCE record with item_id and table_name as top-level fields.
# self/cls are excluded automatically for methods.
```

---

## Stdlib compatibility

`logging.getLogger(__name__)` works everywhere — no migration required:

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Still works", extra={"key": "value"})
# extra={} fields are flattened into the JSON record automatically
```

### PERFORMANCE level for stdlib loggers

```python
from pleasant_loggers import add_performance_level
import logging

add_performance_level()   # explicit opt-in — not called automatically
logger = logging.getLogger(__name__)
logger.performance("Step complete", process_id="etl_1")
```

---

## Processor chain

The shared processor chain (in order):

```
ExtraAdder              → flatten extra={} from stdlib LogRecord
KeyCollisionGuard       → raise KeyError on reserved field conflicts
JsonSerializabilityGuard → raise TypeError on non-JSON-serializable values
add_log_level           → inject "level" field
add_logger_name         → inject "logger" field
CallsiteParameterAdder  → inject "module", "func_name", "lineno"
TimeStamper(fmt="iso")  → inject "timestamp"
format_exc_info         → format exceptions
[JSONRenderer | ConsoleRenderer]  → per handler
```

**Reserved fields** (cannot be passed as kwargs): `timestamp`, `level`, `logger`, `module`, `func_name`, `lineno`, `exception`

---

## LogReader

Parse and analyse NDJSON log files. Requires `pip install pleasant-loggers[analysis]`.

```python
from pleasant_loggers import LogReader

reader = LogReader(log_controller.json_file_path).load()

# Full DataFrame
df = reader.to_df()

# Filter on any combination of axes
reader.filter(level="error")
reader.filter(level=["error", "critical"], start="2026-03-01", end="2026-03-31")
reader.filter(func_name="run_batch")
reader.filter(module="database_manager")

# Performance analysis
reader.performance_summary()     # avg/min/max duration_ms grouped by func_name
reader.activity_timeline("run_batch")  # all records for a function, sorted by timestamp
```

`LogReader` accepts any flat NDJSON file — not just files produced by `pleasant_loggers`. Unknown fields become nullable DataFrame columns.

---

## CLI

```bash
pleasant-logs data/logs/run.json.log --level ERROR
pleasant-logs data/logs/run.json.log --level PERFORMANCE --summary
pleasant-logs data/logs/run.json.log --func run_batch --start 2026-03-01 --output results.csv
```

Options:

| Flag | Description |
|---|---|
| `--level LEVEL [...]` | Filter by one or more log levels |
| `--func FUNC_NAME` | Filter by function name |
| `--start ISO_DATE` | Include records at or after this datetime |
| `--end ISO_DATE` | Include records at or before this datetime |
| `--summary` | Print `performance_summary()` table |
| `--output FILE` | Write filtered output to CSV |

---

## Log file utilities

```python
from pleasant_loggers import get_log_directories, get_log_files, delete_todays_logs, clear_logs

get_log_directories()    # list of directories inside data/logs/
get_log_files()          # dict: directory -> list of .log file names
delete_todays_logs()     # delete today's log directory
clear_logs()             # delete all log directories
```

---

## Version history

- **2.0.0** — Full rewrite. structlog processor engine, dataclass-based modes, `get_logger()` with `perf()`/`timed()`, flat NDJSON output, `LogReader` replacing `JSONLogParser`, CLI entry point. Breaking change.
- 1.5: Rename modes; add `file`, `json`, `json_level`, `file_format`, `rotating` overrides
- 1.4: Add `LoggingMode` enum; `TimedRotatingFileHandler` support; configure_logging keyword overrides
- 1.3: Rewrite `HandlerController` and tests; add `_reset()` for test isolation; add PERFORMANCE log level
- 1.2: Add `configure_logging`, JSON log generation, and `JSONLogParser`
- 1.1: Deprecate `Logger` class
- 1.0: Initial release

## License

MIT — see LICENSE for details.
