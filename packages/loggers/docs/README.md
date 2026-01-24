# Project Title

Loggers

## Description

Loggers is a modified logging package that is designed to be flexible and modular.
The package is designed to be used in a generic python project as a way to handle run logs in a
sophisticated and organized way.

### Main Components

Logger: logging wrapper for logger handling
**NOTE: Logger is redundant/depracated. Do not use.**
While the original package contained a Logger wrapper class,
the package has been updated to integrate more smoothly with the native logging library.
The wrapper has been replaced by helper functions to set up log handlers and configurations

LogHandlerController: This ensures that all loggers share the same run name and log file paths. Handles joining of new handlers.

configure_logger(): This class is used to ensure that all loggers send their logs to the same files.

JSONLogParser: Class that reads, filters, and interprets a JSON log file.

### Usage

#### configure_logger

```python
import logging

logger = logging.getLogger(__name__)
log_handler_controller = configure_logger(logger)
```

- Once configured, use logger as normal.
- A 'performance' method is added during configuration which allows for moe specific performance logging / parsing. Enabled special kwarg process_id for filtering later.
- The process_id is added to the extra dict under the key 'process_id'.

```python
logging.performance("Measuring performance or process", process_id="processing_time")
```

#### JSONLogParser

- Once logs have been generated, JSONLogParser can be created to filter through the logs.

```python
json_file_path = log_handler_controller.json_file_path
parser = JSONLogParser(json_file_path)
json_parser.load()
```

- Before any heavy lifting, the load() method must be called to pull and normalize the log records.
- The load() method will clear any metrics or logs already loaded in the parser.
- Once loaded, there are a variety of methods available to filter the logs records which are stored as a list of LogRecord dataclass objects.

```python
json_parser.filter_by_level("DEBUG")

json_parser.filter_by_time(start_time=datetime(), end_time=datetime())

json_parser.get_extra(record, key, default) # Extracts the value associated with the key in the extra dict if present.

json_parser.filter_by_extra(key) # Returns a list of LogRecords with the key present in the extra dict.

json_parser.get_records_by_id([record_ids])

json_parser.top_messages(n) # Returns the n messages with the highest frequency.

# A number of basic metrics are recorded like the number of times each log level is called or a given funciton is called.
json_parser.level_counts()
json_parser.func_counts()
json_parser.module_counts()

# Converts the given list of records to a dataframe or the json_parser.records if none provided
json_parser.to_dataframe(list[LogRecord] | None) 
```

## Challenges

- instance versus class attribute management
- deciding allocation of class versus instance methods
- generalizing code for use in multiple projects and situaitons
- machine readable log generation and basic parsing
- integrating new functionality with native Python library
- test development

## Version History

- 1.0: initial release
- 1.1: Deprecate Logger class in place of logging setup helper functions.
- 1.2: Adds new config_logge, json log feneration, and JSONLogParse functionality

## Future Releases

- Further simplify log configuration step to act on root
- Add class or methods to cleanly handle performance logs

## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## Logger Usage (Deprecated)

```python
Import Logger class:
from loggers import Logger
```

Set the overall run name at the top level of your program:

```python
Logger.set_run_name(run_name)
```

Create Logger instane:

```python
logger = Logger(logger_name)
```

Add join or remove handlers:

```python
logger.add_console_handler(handler_name)
logger.add_file_handler(handler_name: str = "main")
logger.join_handler(other_logger_name, handler_name)
logger.remove_hanler(handler_name)
```

Use logger as normal

```python
logger.debug(message)
logger.info(message)
logger.warning(message)
logger.error(message)
logger.critical(message)
```

Clear log files

```python
logger.clear_todays_logs()
logger.clear_all_logs()
```
