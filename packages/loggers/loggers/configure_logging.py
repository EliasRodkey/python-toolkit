"""
Docstring for loggers.configure_logger.py

This module contains functions that are used to control and standardize
logger configurations across modules and projects.

Functions:
    configure_logger (logger: logging.Logger): Configures a given logger with prefered handlers and formatting.
"""
# Standard library imports
import logging

# Local imports
from loggers.handler_controller import HandlerController
from loggers.utils import LOG_FILE_DEFAULT_DIRECTORY, LoggingMode, add_performance_level

# Mode defaults: all handler options keyed by name
_MODE_DEFAULTS = {
    LoggingMode.DIRECTORY_PER_RUN: {
        "stream":       True,
        "stream_level": logging.INFO,
        "file_level":   logging.DEBUG,
        "json_level":   logging.DEBUG,
        "rotating":     False,
        "json":         True,
    },
    LoggingMode.DAILY_DIRECTORY: {
        "stream":       False,
        "stream_level": logging.INFO,
        "file_level":   logging.DEBUG,
        "json_level":   logging.DEBUG,
        "rotating":     False,
        "json":         True,
    },
    LoggingMode.BASIC_ROTATING_HANDLER: {
        "stream":       True,
        "stream_level": logging.WARNING,
        "file_level":   logging.DEBUG,
        "json_level":   logging.DEBUG,
        "rotating":     True,
        "json":         True,
    },
}


def configure_logging(
        log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
        mode: LoggingMode = LoggingMode.DIRECTORY_PER_RUN,
        stream: bool | None = None,
        stream_level: int | None = None,
        file_level: int | None = None,
        json_level: int | None = None,
        rotating: bool | None = None,
        json: bool | None = None,
        ) -> HandlerController:
    """
    Configures the root logger with standardized handlers and formatting.

    Args:
        log_directory (str): Parent folder for all logs. Defaults to cwd/data/logs/.
        mode (LoggingMode): Logging profile that sets defaults for all other options.
            DIRECTORY_PER_RUN (default): per-run timestamped folder, INFO stream.
            DAILY_DIRECTORY: single daily folder, no stream handler.
            BASIC_ROTATING_HANDLER: flat directory with TimedRotatingFileHandler, WARNING stream.
        stream (bool | None): Override whether a stream handler is added. Defaults to mode setting.
        stream_level (int | None): Override stream handler log level. Defaults to mode setting.
        file_level (int | None): Override text file handler log level. Defaults to mode setting.
        json_level (int | None): Override JSON file handler log level. Defaults to mode setting.
        rotating (bool | None): Override whether to use TimedRotatingFileHandler. Defaults to mode setting.
        json (bool | None): Override whether to include a JSON file handler. Defaults to mode setting.

    Returns:
        HandlerController: Manages handlers and file paths for the current run.
    """
    add_performance_level()

    # Resolve final settings: explicit kwargs override mode defaults
    defaults = _MODE_DEFAULTS[mode]
    resolved_stream = stream if stream is not None else defaults["stream"]
    resolved_stream_level = stream_level if stream_level is not None else defaults["stream_level"]
    resolved_file_level = file_level if file_level is not None else defaults["file_level"]
    resolved_json_level = json_level if json_level is not None else defaults["json_level"]
    resolved_rotating = rotating if rotating is not None else defaults["rotating"]
    resolved_json = json if json is not None else defaults["json"]

    log_controller = HandlerController(
        log_directory=log_directory,
        mode=mode,
        stream=resolved_stream,
        stream_level=resolved_stream_level,
        file_level=resolved_file_level,
        json_level=resolved_json_level,
        rotating=resolved_rotating,
        json=resolved_json,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    root_logger.addHandler(log_controller.get_handler("main"))
    if log_controller.json_file_handler is not None:
        root_logger.addHandler(log_controller.json_file_handler)
    if log_controller.stream_handler is not None:
        root_logger.addHandler(log_controller.stream_handler)

    root_logger.propagate = False

    return log_controller