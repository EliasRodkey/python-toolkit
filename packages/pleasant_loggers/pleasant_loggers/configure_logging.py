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
from pleasant_loggers.handler_controller import HandlerController
from pleasant_loggers.utils import LOG_FILE_DEFAULT_DIRECTORY, LoggingFormats, LoggingMode, add_performance_level

# Mode defaults: all handler options keyed by name
_MODE_DEFAULTS = {
    LoggingMode.BASIC_SINGLE_FILE: {
        "stream": True,
        "stream_level": logging.INFO,
        "file_level": logging.DEBUG,
        "json_level": logging.DEBUG,
        "file_format": LoggingFormats.FORMAT_BASIC,
        "rotating": False,
        "file": True,
        "json": False,
    },
    LoggingMode.BASIC_JSON_FILE: {
        "stream": True,
        "stream_level": logging.INFO,
        "file_level": logging.DEBUG,
        "json_level": logging.DEBUG,
        "file_format": LoggingFormats.FORMAT_BASIC,
        "rotating": False,
        "file": False,
        "json": True,
    },
    LoggingMode.DIRECTORY_PER_RUN: {
        "stream": True,
        "stream_level": logging.INFO,
        "file_level": logging.INFO,
        "json_level": logging.DEBUG,
        "file_format":LoggingFormats.FORMAT_BASIC,
        "rotating": False,
        "file": True,
        "json": True,
    },
    LoggingMode.DAILY_DIRECTORY: {
        "stream": False,
        "stream_level": logging.INFO,
        "file_level": logging.DEBUG,
        "json_level": logging.DEBUG,
        "file_format": LoggingFormats.FORMAT_BASIC,
        "rotating": False,
        "file": True,
        "json": True,
    },
    LoggingMode.BASIC_ROTATING_HANDLER: {
        "stream": True,
        "stream_level": logging.WARNING,
        "file_level": logging.DEBUG,
        "json_level": logging.DEBUG,
        "file_format": LoggingFormats.FORMAT_BASIC,
        "rotating": True,
        "file": True,
        "json": True,
    },
}


def configure_logging(
        log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
        mode: LoggingMode = LoggingMode.BASIC_SINGLE_FILE,
        stream: bool | None = None,
        stream_level: int | None = None,
        file_level: int | None = None,
        json_level: int | None = None,
        file_format: LoggingFormats=None,
        rotating: bool | None = None,
        file: bool | None = None,
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
        file_format (LoggingFormats | None): The format the file handler will output
        rotating (bool | None): Override whether to use TimedRotatingFileHandler. Defaults to mode setting.
        file (bool | None): Override whether to include a file handler. Defaults to mode setting.
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
    resolved_file_format = file_format if file_format is not None else defaults["file_format"]
    resolved_rotating = rotating if rotating is not None else defaults["rotating"]
    resolved_file = file if file is not None else defaults["file"]
    resolved_json = json if json is not None else defaults["json"]

    log_controller = HandlerController(
        log_directory=log_directory,
        mode=mode,
        stream=resolved_stream,
        stream_level=resolved_stream_level,
        file_level=resolved_file_level,
        json_level=resolved_json_level,
        file_format=resolved_file_format,
        rotating=resolved_rotating,
        file=resolved_file,
        json=resolved_json,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if "main" in log_controller.handler_names():
        root_logger.addHandler(log_controller.get_handler("main"))
    if log_controller.json_file_handler is not None:
        root_logger.addHandler(log_controller.json_file_handler)
    if log_controller.stream_handler is not None:
        root_logger.addHandler(log_controller.stream_handler)

    root_logger.propagate = False

    return log_controller