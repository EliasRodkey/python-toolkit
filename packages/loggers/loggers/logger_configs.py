"""
Docstring for loggers.logger_configs.py

This module contians functions and classes that are used to control  and standardize
logger configurations across modules and projects.

Classes:
    JSONFormatter: A custom logging formatter that outputs logs in JSON format.
    LogFileNameController: A singleton like class that manages log file names and paths to ensure consistency across loggers.

Functions:
    configure_logger (logger: logging.Logger): Configures a given logger with prefered handlers and formatting.
"""
# Built in imports
from datetime import datetime
import json
import logging
import os

# Package level imports
from loggers.utils import ELoggingFormats, LOG_FILE_DEFAULT_DIRECTORY, create_datestamp, create_log_datetime_stamp



class StructuredLogger(logging.Logger):
    def makeRecord(
        self,
        name,
        level,
        fn,
        lno,
        msg,
        args,
        exc_info,
        func=None,
        extra=None,
        sinfo=None,
    ):
        record = super().makeRecord(
            name, level, fn, lno, msg, args, exc_info, func, extra, sinfo
        )

        record.context = extra or {}
        return record



class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "exception": self.formatException(record.exc_info) if record.exc_info else "",
            "extra": getattr(record, "context", {}),
        })



class LoggingHandlerController():
    """
    This class is used to ensure that all loggers send their logs to the same files.
    This ensures that all loggers share the same run name and log file paths.
    It creates a daily log folder and run folders within it with unique datetime stamps.
    It also creates a universal json log file hander for all loggers to use as well as a stream handler.
    It also creates individual readable log file paths and handlers for each unique run name.

    Attributes:
        run_name (str): The name of the run given at instantiation. defaults to "main". 
                        If the run name already exists, the class returns the same path and handler from the last instance.
        instance_run_info (dict): A dictionalry with keys "path" and "handler" that contain the file path and handler for the readable log of the given run_name.

    Properties:
        run_directory (str): The path to the directory that contains all of the log files for the current run.
        readable_file_path (str): The path to the readable log file of the given run_name.
        readable_file_handler (logging.FileHandler): FileHandler for readable log file of the given run_name. 
        json_file_path (str): The path to the json log file (same for all instances).
        json_file_handler (logging.FileHandler): FileHandler for json log file (same for all instances). 
        stream_handler (logging.StreamHandler): StreamHandler for all instances
        handlers (dict): A dictionary of the handlers handled by this class
    """
    _run_names: dict = {}
    _daily_log_stamp: str = ""
    _log_datetime_stamp: str = ""
    _run_directory: str = ""
    _json_file_path: str = ""
    _json_file_handler: logging.FileHandler = None
    _stream_handler: logging.StreamHandler = None
    _initialized: bool = False

    def __new__(cls, run_name: str, text_formatter: logging.Formatter, log_directory: str):
        """If this is the first time the class is being instantiated, set up the daily log folder and json log file path."""
        if cls._initialized == False:
            cls._daily_log_stamp = create_datestamp() # Daily log folder
            cls._log_datetime_stamp = create_log_datetime_stamp() # Log folder within the daily log folder
            cls._run_directory = os.path.join(log_directory, cls._daily_log_stamp, cls._log_datetime_stamp)
            os.makedirs(cls._run_directory, exist_ok=True) # Create the run directory if it doesn't exist
            
            # Create the json og file handler (used by all loggers in the run)
            cls._json_file_path = os.path.join(cls._run_directory, f"{cls._log_datetime_stamp}.json.log")
            cls._json_file_handler = logging.FileHandler(cls._json_file_path)
            cls._json_file_handler.setFormatter(JSONFormatter())
            cls._json_file_handler.setLevel(logging.DEBUG)

            # Create the stream handler (used by all loggers unless specified otherwise) sets level to INFO
            cls._stream_handler = logging.StreamHandler()
            cls._stream_handler.setFormatter(text_formatter)
            cls._stream_handler.setLevel(logging.INFO)

            cls._initialized = True
        
        os.makedirs(cls._run_directory, exist_ok=True) # Create the run directory if it doesn't exist
        
        return super(LoggingHandlerController, cls).__new__(cls)


    def __init__(self, run_name: str, text_formatter: logging.Formatter, log_directory: str):
        """Each time this class is instantiated, check to see if the run name is already in use. If so, use the existing file paths. If not create new."""
        # Access class variables directly from class to avoid accidental reasaignment
        cls = type(self)
        if run_name not in cls._run_names:
            # Create readable file path and handler for new run names
            readable_file_path = os.path.join(cls._run_directory, f"{cls._log_datetime_stamp}_{run_name}.log")
            readable_text_handler = logging.FileHandler(readable_file_path)
            readable_text_handler.setFormatter(text_formatter)
            readable_text_handler.setLevel(logging.DEBUG)
            cls._run_names[run_name] = {
                "path" : readable_file_path,
                "handler" : readable_text_handler
                }
        
        self.run_name = run_name
        self.instance_run_info = cls._run_names[run_name]
    

    @property
    def run_directory(self) -> str:
        """Returns the path to the directory for the log files of the current run as a string"""
        return self._run_directory

    @property
    def readable_file_path(self) -> str:
        """Returns the readable log file path."""
        return self.instance_run_info["path"]


    @property
    def readable_file_handler(self) -> logging.FileHandler:
        """Returns a file handler for the readable log file path."""
        return self.instance_run_info["handler"]


    @property
    def json_file_path(self) -> str:
        """Returns the json log file path."""
        return self._json_file_path
    

    @property
    def json_file_handler(self) -> logging.FileHandler:
        """Returns a file handler for the json log file path."""
        return self._json_file_handler
    

    @property
    def stream_handler(self) -> logging.StreamHandler:
        """Returns the stream handler for standard output."""
        return self._stream_handler


    @property
    def handlers(self) -> dict[str, logging.Handler]:
        """Returns a dictionary of the handlers handled by this class"""
        cls = type(self)
        return {
            "json" : self.json_file_handler,
            "readable" : {name: run["handler"] for name, run in cls._run_names.items()},
            "stream" : self.stream_handler
        }
    


def configure_logger(
        logger: logging.Logger, 
        run_name: str="main", 
        format: ELoggingFormats=ELoggingFormats.FORMAT_BASIC, 
        add_to_stream: bool=True,
        log_direcotry: str=LOG_FILE_DEFAULT_DIRECTORY
        ) -> LoggingHandlerController:
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
    log_controller = LoggingHandlerController(run_name, text_formatter, log_direcotry)

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