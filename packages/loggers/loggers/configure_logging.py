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

# Mode defaults: (stream_enabled, stream_level, file_level)
_MODE_DEFAULTS = {
    LoggingMode.DEVELOPMENT: (True,  logging.INFO,    logging.DEBUG),
    LoggingMode.TEST:        (False, logging.INFO,    logging.DEBUG),
    LoggingMode.PRODUCTION:  (True,  logging.WARNING, logging.DEBUG),
}


def configure_logging(
        log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
        mode: LoggingMode = LoggingMode.DEVELOPMENT,
        stream: bool | None = None,
        stream_level: int | None = None,
        file_level: int | None = None,
        ) -> HandlerController:
    """
    Configures the root logger with standardized handlers and formatting.

    Args:
        log_directory (str): Parent folder for all logs. Defaults to cwd/data/logs/.
        mode (LoggingMode): Logging profile. DEVELOPMENT (default) creates a per-run folder.
            TEST uses a daily folder with no stream handler.
            PRODUCTION uses TimedRotatingFileHandler with WARNING-level stream output.
        stream (bool | None): Override whether a stream handler is added. Defaults to mode setting.
        stream_level (int | None): Override stream handler log level. Defaults to mode setting.
        file_level (int | None): Override file handler log level. Defaults to mode setting.

    Returns:
        HandlerController: Manages handlers and file paths for the current run.
    """
    add_performance_level()

    # Resolve final settings: explicit kwargs override mode defaults
    default_stream, default_stream_level, default_file_level = _MODE_DEFAULTS[mode]
    resolved_stream = stream if stream is not None else default_stream
    resolved_stream_level = stream_level if stream_level is not None else default_stream_level
    resolved_file_level = file_level if file_level is not None else default_file_level

    log_controller = HandlerController(
        log_directory=log_directory,
        mode=mode,
        stream=resolved_stream,
        stream_level=resolved_stream_level,
        file_level=resolved_file_level,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    root_logger.addHandler(log_controller.get_handler("main"))
    root_logger.addHandler(log_controller.json_file_handler)
    if log_controller.stream_handler is not None:
        root_logger.addHandler(log_controller.stream_handler)

    root_logger.propagate = False

    return log_controller