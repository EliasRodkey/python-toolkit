'''
Docstring for loggers.logger_configs.py

This module contians functions and classes that are used to control  and standardize
logger configurations across modules and projects.

Classes:
    JSONFormatter: A custom logging formatter that outputs logs in JSON format.
    LogFileNameController: A singleton like class that manages log file names and paths to ensure consistency across loggers.

Functions:
    configure_logger (logger: logging.Logger): Configures a given logger with prefered handlers and formatting.
'''
# Built in imports
from datetime import datetime
import json
import logging
import os

# Package level imports
from loggers.utils import ELoggingFormats, LOG_FILE_DEFAULT_DIRECTORY, create_datestamp, create_log_datetime_stamp



class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat() + "Z",
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'extra': ''
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra"):
            log_record["extra"] = record.extra

        return json.dumps(log_record)



class LoggingHandlerController():
    '''
    This class is used to ensure that all loggers send their logs to the same files.
    This ensures that all loggers share the same run name and log file paths.
    It creates a daily log folder and run folders within it with unique datetime stamps.
    It also creates a universal json log file hander for all loggers to use as well as a stream handler.
    It also creates individual readable log file paths and handlers for each unique run name.
    '''
    _run_names: dict = {}
    _daily_log_stamp: str = ''
    _log_datetime_stamp: str = ''
    _run_directory: str = ''
    _json_log_file_path: str = ''
    _json_file_handler: logging.FileHandler = None
    _stream_handler: logging.StreamHandler = None
    _initialized: bool = False

    def __new__(cls, run_name: str, text_formatter: logging.Formatter):
        '''If this is the first time the class is being instantiated, set up the daily log folder and json log file path.'''
        if cls._initialized == False:
            cls._daily_log_stamp = create_datestamp() # Daily log folder
            cls._log_datetime_stamp = create_log_datetime_stamp() # Log folder within the daily log folder
            cls._run_directory = os.path.join(LOG_FILE_DEFAULT_DIRECTORY, cls._daily_log_stamp, cls._log_datetime_stamp)
            os.makedirs(cls._run_directory, exist_ok=True) # Create the run directory if it doesn't exist

            # Create the json og file handler (used by all loggers in the run)
            cls._json_log_file_path = os.path.join(cls._run_directory, f'{cls._log_datetime_stamp}.json.log')
            cls._json_file_handler = logging.FileHandler(cls._json_log_file_path)
            cls._json_file_handler.setFormatter(JSONFormatter())

            # Create the stream handler (used by all loggers unless specified otherwise) sets level to INFO
            cls._stream_handler = logging.StreamHandler()
            cls._stream_handler.setFormatter(text_formatter)
            cls._stream_handler.setLevel(logging.INFO)

            cls._initialized = True
        
        return super(LoggingHandlerController, cls).__new__(cls)


    def __init__(self, run_name: str, text_formatter: logging.Formatter):
        '''Each time this class is instantiated, check to see if the run name is already in use. If so, use the existing file paths. If not create new.'''
        if run_name not in self._run_names.keys():
            self._run_names[run_name] = {
                'path' : os.path.join(self._run_directory, f'{self._log_datetime_stamp}_{run_name}.log'),
                'handler' : logging.FileHandler(self.readable_log_file_path)
                }
        
        self.run_name = run_name
        self.text_formatter = text_formatter
        self.instance_run = self._run_names[run_name]
    

    @property
    def readable_file_path(self) -> str:
        '''Returns the readable log file path.'''
        return self.instance_run['path']


    @property
    def readable_file_handler(self) -> logging.FileHandler:
        '''Returns a file handler for the readable log file path.'''
        handler = self.instance_run['handler']
        handler.setFormatter(self.text_formatter)
        return handler


    @property
    def json_log_file_path(self) -> str:
        '''Returns the json log file path.'''
        return self._json_log_file_path
    

    @property
    def json_file_handler(self) -> logging.FileHandler:
        '''Returns a file handler for the json log file path.'''
        return self._json_file_handler
    

    @property
    def stream_handler(self) -> logging.StreamHandler:
        '''Returns the stream handler for standard output.'''
        return self._stream_handler
    


def configure_logger(logger: logging.Logger, run_name: str='main', format: ELoggingFormats=ELoggingFormats.FORMAT_BASIC, add_to_stream: bool=True) -> None:
    '''
    Configures a given logger with prefered handlers and formatting.
    Includes a stream handler with standard output (level: INFO),
    a file handler with DEBUG level logging to a default log directory,
    and a json file handler with DEBUG level logging to a default log directory.
    Also adds a PERFORMANCE logging level to the logger for performance metrics.

    Args:
        logger (logging.Logger): The logger instance to configure.
    '''
    text_formatter = logging.Formatter(format)
    log_controller = LoggingHandlerController(run_name, text_formatter, add_to_stream)

    # Add handlers to the logger
    logger.addHandler(log_controller.readable_file_handler)
    logger.addHandler(log_controller.json_file_handler)

    if add_to_stream:
        logger.addHandler(log_controller.stream_handler)
    
    # Ensure the logger does not create duplicate entries
    logger.propagate = False