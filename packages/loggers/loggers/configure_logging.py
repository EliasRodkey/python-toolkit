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
from loggers.utils import LOG_FILE_DEFAULT_DIRECTORY, add_performance_level


def configure_logging(
        log_directory: str=LOG_FILE_DEFAULT_DIRECTORY
        ) -> HandlerController:
    """
    Configures a given logger with prefered handlers and formatting.
    Includes a stream handler with standard output (level: INFO),
    a file handler with DEBUG level logging to a default log directory,
    and a json file handler with DEBUG level logging to a default log directory.
    Also adds a PERFORMANCE logging level to the logger for performance metrics.

    Args:
        log_directory (str): the parent folder for all logs, defaults to cwd/data/logs/.

    Returns:
        LoggingHandlerController: class that contains handlers and file paths to the log files associated with the current run.
    """
    # Add performance level logging
    add_performance_level()

    log_controller = HandlerController(log_directory=log_directory)

    # Configure root logger with standardized handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Add handlers to the logger
    root_logger.addHandler(log_controller.get_handler("main"))
    root_logger.addHandler(log_controller.json_file_handler)
    root_logger.addHandler(log_controller.stream_handler)
    
    # Ensure the logger does not create duplicate entries
    root_logger.propagate = False

    return log_controller