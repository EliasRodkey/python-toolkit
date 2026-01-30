"""
Docstring for loggers.configure_logger.py

This module contians functions and classes that are used to control  and standardize
logger configurations across modules and projects.

Functions:
    configure_logger (logger: logging.Logger): Configures a given logger with prefered handlers and formatting.
"""
# Standard library imports
import logging

# Local imports
from loggers.handler_controller import HandlerController
from loggers.utils import ELoggingFormats

def configure_logger(
        logger: logging.Logger, 
        run_name: str="main", 
        format: ELoggingFormats=ELoggingFormats.FORMAT_BASIC, 
        add_to_stream: bool=True,
        log_direcotry: str=LOG_FILE_DEFAULT_DIRECTORY
        ) -> HandlerController:
    """
    Configures a given logger with prefered handlers and formatting.
    Includes a stream handler with standard output (level: INFO),
    a file handler with DEBUG level logging to a default log directory,
    and a json file handler with DEBUG level logging to a default log directory.
    Also adds a PERFORMANCE logging level to the logger for performance metrics.

    Args:
        logger (logging.Logger): The logger instance to configure.
        run_name (str): name for the run. Determines which file handler the logger will output to. defaults to "main".
        format (ELoggingFormats): a string containing the desired logging output format
        add_to_stream (bool): Whether or not the logger should output to the console
        log_directory (str): the parent folder for all logs, defaults to cwd/data/logs/.

    Returns:
        LoggingHandlerController: class that contains handlers and file paths to the log files associated with the current run.
    """
    text_formatter = logging.Formatter(format)
    log_controller = HandlerController(run_name, text_formatter, log_direcotry)

    # Set the default logger level to DEBUG
    logger.setLevel(logging.DEBUG)

    # Add handlers to the logger
    logger.addHandler(log_controller.readable_file_handler)
    logger.addHandler(log_controller.json_file_handler)

    if add_to_stream:
        logger.addHandler(log_controller.stream_handler)
    
    # Ensure the logger does not create duplicate entries
    logger.propagate = False

    return log_controller