"""
Docstring for loggers.logging_handler_controller.py

This module contians functions and classes that are used to control  and standardize
logger handlers across modules and projects.

Classes:
    StructuredLogger: A custom logger class that adds an 'extra' context dictionary to log records.
    JSONFormatter: A custom logging formatter that outputs logs in JSON format.
    LogFileNameController: A singleton like class that manages log file names and paths to ensure consistency across loggers.
"""
# Standard library imports
from datetime import datetime
import json
import logging
import os
from typing import Tuple, List

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



class HandlerController():
    """
    This class is used to ensure that all loggers send their logs to the same files.
    This ensures that all loggers share the same run name and log file paths.
    It creates a daily log folder and run folders within it with unique datetime stamps.
    It also creates a universal json log file hander for all loggers to use as well as a stream handler.
    It also creates individual readable log file paths and handlers for each unique run name.

    Attributes:
        run_directory (str): The path to the directory that contains all of the log files for the current run.
        json_file_path (str): The path to the json log file (same for all instances).
        json_file_handler (logging.FileHandler): FileHandler for json log file (same for all instances). 
        stream_handler (logging.StreamHandler): StreamHandler for all instances

    Methods:
        add_file_handler: Adds a file handler to the Handler Controller

    Properties:
        handlers_names (list): A list of the handler names handled by this class
    """
    handlers: dict = {}
    log_datetime_stamp: str = ""
    run_directory: str = ""
    json_file_path: str = ""
    json_file_handler: logging.FileHandler 
    stream_handler: logging.StreamHandler
    _initialized: bool = False

    def __new__(cls, log_directory: str=LOG_FILE_DEFAULT_DIRECTORY):
        """If this is the first time the class is being instantiated, set up the daily log folder and json log file path."""
        if cls._initialized == False:
            # Generate log folder and return datetime stmap + directory
            cls.log_datetime_stamp, cls.run_directory = cls._generate_program_run_folder(log_directory)
            
            # Create the json og file handler (used by all loggers in the run)
            cls.json_file_path, cls.json_file_handler = cls._create_json_log_handler()

            # Create the stream handler (used by all loggers unless specified otherwise) sets level to INFO
            cls.stream_handler = cls._create_stream_log_handler()

            # Mark that the class has been initialized once and these values should be set
            cls._add_handler("json", cls.json_file_handler)
            cls._add_handler("stream", cls.stream_handler)
            cls.add_file_handler("main")
            cls._initialized = True
        
        os.makedirs(cls.run_directory, exist_ok=True) # Create the run directory if it doesn't exist
        
        return super(HandlerController, cls).__new__(cls)
    
    @classmethod
    def _generate_program_run_folder(cls, log_directory: str) -> Tuple[str, str]:
        """Generates the log direcotry and log datetime stamps for future handlers"""
        daily_log_stamp = create_datestamp() # Daily log folder
        log_datetime_stamp = create_log_datetime_stamp() # Log folder within the daily log folder
        run_directory = os.path.join(log_directory, daily_log_stamp, log_datetime_stamp)
        os.makedirs(run_directory, exist_ok=True) # Create the run directory if it doesn't exist
        return (log_datetime_stamp, run_directory)

    @classmethod
    def _create_json_log_handler(cls) -> Tuple[str, logging.FileHandler]:
        """Creates universal json file handler"""
        json_file_path = os.path.join(cls.run_directory, f"{cls.log_datetime_stamp}.json.log")
        json_file_handler = logging.FileHandler(json_file_path)
        json_file_handler.setFormatter(JSONFormatter())
        json_file_handler.setLevel(logging.DEBUG)
        return (json_file_path, json_file_handler)

    @classmethod
    def _create_stream_log_handler(cls) -> logging.StreamHandler:
        """Creates universal INFO level stream handler"""
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(ELoggingFormats.FORMAT_BASIC)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        return stream_handler
    
    @classmethod
    def add_file_handler(cls, run_name: str, text_format: str=ELoggingFormats.FORMAT_BASIC):
        """Adds a file handler to the Handler Controller"""
        readable_file_path = os.path.join(cls.run_directory, f"{cls.log_datetime_stamp}_{run_name}.log")
        readable_text_handler = logging.FileHandler(readable_file_path)
        formatter = logging.Formatter(text_format)
        readable_text_handler.setFormatter(formatter)
        readable_text_handler.setLevel(logging.DEBUG)
        cls._add_handler(run_name, readable_text_handler)
    
    @classmethod
    def get_handler(cls, key: str):
        if key in cls.handlers:
            return cls.handlers[key]
        else:
            raise KeyError(f"Key {key} does not exists in handlers: {list(cls.handlers.keys())}")
    
    @classmethod
    def remove_handler(cls, name):
        if name in cls.handlers:
            cls.handlers[name].flush()
            cls.handlers[name].close()
            del cls.handlers[name]
        else:
            raise KeyError(f"Cannot remove {name} from handlers: {list(cls.handlers.keys())}")
    
    @classmethod
    def _add_handler(cls, name: str, handler: logging.Handler):
        """Adds a handler to the handlers dict"""
        if name not in cls.handlers:
            cls.handlers[name] = handler
        else:
            raise KeyError(f"Handler {name} already in handlers: {list(cls.handlers.keys())}")
        
    @classmethod
    def _reset(cls):
        """Resets class variables. Used for testing."""
        # Close any stored handlers (readable/stream)
        handlers = getattr(cls, "handlers", {}) or {}
        for k, h in list(handlers.items()):
            try:
                h.flush()
                h.close()
            except Exception:
                pass
        cls.handlers = {}

        # If the class has been initialized at some point we can safely reset.
        if cls._initialized:
            cls.log_datetime_stamp = ""
            cls.run_directory = ""
            cls.json_file_path = ""
            cls.stream_handler = None
            cls.json_file_handler = None

        # Reset initialization to False
        cls._initialized = False
        


    def __init__(self, log_directory: str=LOG_FILE_DEFAULT_DIRECTORY):
        self.log_directory = log_directory
    

    def handler_names(self) -> List[str]:
        """Returns a list of the handler names in handlers"""
        return list(self.handlers.keys())
    
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.run_directory})"