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
from logging.handlers import TimedRotatingFileHandler
import os
from typing import Tuple, List

# Package level imports
from loggers.utils import ELoggingFormats, LOG_FILE_DEFAULT_DIRECTORY, LoggingMode, create_datestamp, create_log_datetime_stamp



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

    In DEVELOPMENT mode (default): creates a timestamped run folder per process.
    In TEST mode: uses a single daily folder (no per-run subfolder).
    In PRODUCTION mode: uses TimedRotatingFileHandler with daily rotation.

    Attributes:
        run_directory (str): The path to the directory that contains all of the log files for the current run.
        json_file_path (str): The path to the json log file (same for all instances).
        json_file_handler (logging.FileHandler): FileHandler for json log file (same for all instances).
        stream_handler (logging.StreamHandler): StreamHandler for all instances (None if stream=False).
        mode (LoggingMode): The active logging mode.

    Methods:
        add_file_handler: Adds a file handler to the Handler Controller
    """
    handlers: dict = {}
    log_datetime_stamp: str = ""
    run_directory: str = ""
    json_file_path: str = ""
    json_file_handler: logging.FileHandler
    stream_handler: logging.StreamHandler
    mode: LoggingMode = LoggingMode.DEVELOPMENT
    _initialized: bool = False

    def __new__(
        cls,
        log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
        mode: LoggingMode = LoggingMode.DEVELOPMENT,
        stream: bool = True,
        stream_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
    ):
        """If this is the first time the class is being instantiated, set up the log folder and handlers."""
        if cls._initialized == False:
            cls.mode = mode

            # Generate log folder and return datetime stamp + directory
            cls.log_datetime_stamp, cls.run_directory = cls._generate_program_run_folder(log_directory, mode)

            # Create the json file handler (used by all loggers in the run)
            cls.json_file_path, cls.json_file_handler = cls._create_json_log_handler(mode, file_level)

            # Create the stream handler (or None if suppressed)
            cls.stream_handler = cls._create_stream_log_handler(stream_level) if stream else None

            # Register handlers
            cls._add_handler("json", cls.json_file_handler)
            if cls.stream_handler is not None:
                cls._add_handler("stream", cls.stream_handler)
            cls.add_file_handler("main", file_level=file_level)
            cls._initialized = True

        os.makedirs(cls.run_directory, exist_ok=True)

        return super(HandlerController, cls).__new__(cls)

    @classmethod
    def _generate_program_run_folder(cls, log_directory: str, mode: LoggingMode) -> Tuple[str, str]:
        """Generates the log directory and datetime stamp based on the active mode."""
        log_datetime_stamp = create_log_datetime_stamp()

        if mode == LoggingMode.DEVELOPMENT:
            # Folder-per-run: data/logs/YYYY-MM-DD/YYYY-MM-DD_HHMMSS/
            daily_log_stamp = create_datestamp()
            run_directory = os.path.join(log_directory, daily_log_stamp, log_datetime_stamp)
        elif mode == LoggingMode.TEST:
            # Daily folder only: data/logs/YYYY-MM-DD/
            daily_log_stamp = create_datestamp()
            run_directory = os.path.join(log_directory, daily_log_stamp)
        else:  # PRODUCTION
            # Flat directory: data/logs/
            run_directory = log_directory

        os.makedirs(run_directory, exist_ok=True)
        return (log_datetime_stamp, run_directory)

    @classmethod
    def _create_json_log_handler(cls, mode: LoggingMode, file_level: int) -> Tuple[str, logging.Handler]:
        """Creates the json file handler. Uses TimedRotatingFileHandler for PRODUCTION mode."""
        if mode == LoggingMode.PRODUCTION:
            json_file_path = os.path.join(cls.run_directory, "loggers.json.log")
            json_file_handler = TimedRotatingFileHandler(
                filename=json_file_path,
                when="midnight",
                backupCount=30,
                encoding="utf-8",
            )
        else:
            json_file_path = os.path.join(cls.run_directory, f"{cls.log_datetime_stamp}.json.log")
            json_file_handler = logging.FileHandler(json_file_path)

        json_file_handler.setFormatter(JSONFormatter())
        json_file_handler.setLevel(file_level)
        return (json_file_path, json_file_handler)

    @classmethod
    def _create_stream_log_handler(cls, level: int = logging.INFO) -> logging.StreamHandler:
        """Creates a stream handler at the given level."""
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(ELoggingFormats.FORMAT_BASIC)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(level)
        return stream_handler

    @classmethod
    def add_file_handler(cls, run_name: str, text_format: str = ELoggingFormats.FORMAT_BASIC, file_level: int = logging.DEBUG):
        """Adds a readable file handler to the Handler Controller."""
        readable_file_path = os.path.join(cls.run_directory, f"{cls.log_datetime_stamp}_{run_name}.log")
        readable_text_handler = logging.FileHandler(readable_file_path)
        formatter = logging.Formatter(text_format)
        readable_text_handler.setFormatter(formatter)
        readable_text_handler.setLevel(file_level)
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
        """Adds a handler to the handlers dict."""
        if name not in cls.handlers:
            cls.handlers[name] = handler
        else:
            raise KeyError(f"Handler {name} already in handlers: {list(cls.handlers.keys())}")

    @classmethod
    def _reset(cls):
        """Resets class variables. Used for testing."""
        handlers = getattr(cls, "handlers", {}) or {}
        for h in list(handlers.values()):
            try:
                h.flush()
                h.close()
            except Exception:
                pass
        cls.handlers = {}

        if cls._initialized:
            cls.log_datetime_stamp = ""
            cls.run_directory = ""
            cls.json_file_path = ""
            cls.stream_handler = None
            cls.json_file_handler = None
            cls.mode = LoggingMode.DEVELOPMENT

        cls._initialized = False


    def __init__(
        self,
        log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
        mode: LoggingMode = LoggingMode.DEVELOPMENT,
        stream: bool = True,
        stream_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
    ):
        self.log_directory = log_directory

    def handler_names(self) -> List[str]:
        """Returns a list of the handler names in handlers"""
        return list(self.handlers.keys())

    def __repr__(self):
        return f"{self.__class__.__name__}({self.run_directory})"