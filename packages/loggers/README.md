# Project Title

Loggers

## Description

Loggers is a modified logging package that is designed to be flexible and modular.
The package is designed to be used in a generic python project as a way to handle run logs in a
sophisticated and organized way.

Logger: creates and manages logging instances and handlers at a high level

LogParse: parses log files for errors

PerformanceLogger: tracks program performance (execution time)

## Challenges

- instance versus class attribute management
- deciding allocation of class versus instance methods
- test development

## Dependencies

- logging
- os
- typing

## Logger Usage

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
logger.add_file_handler(handler_name: str = 'main')
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

## Help

common problems and how to fix them

## Version History

- 1.0: initial release

## Future Releases

- include LogParse class
- include PerformanceLogger class

## License

This project is licensed under the MIT License - see the LICENSE.md file for details
