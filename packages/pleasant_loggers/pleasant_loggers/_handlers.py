"""
pleasant_loggers._handlers

HandlerController: application-scoped singleton that resolves log file paths,
creates stdlib handlers, and exposes json_file_path and log_directory to
downstream consumers (e.g. LogReader, configure_logging).

Public interface:
    controller.json_file_path      — path to the NDJSON log file (or "" if json=False)
    controller.readable_file_path  — path to the human-readable log file (or "" if file=False)
    controller.log_directory       — base log directory passed to configure_logging()
    controller.run_directory       — resolved directory for this run (depends on DirectoryLayout)
    controller.json_file_handler   — stdlib handler for the JSON file (or None)
    controller.readable_file_handler — stdlib handler for the readable text file (or None)
    controller.stream_handler      — stdlib StreamHandler (or None)
    HandlerController._reset()     — for test teardown only
"""
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from typing import Optional, Tuple

from pleasant_loggers._modes import AbstractLoggingMode, DirectoryLayout, DIRECTORY_PER_RUN
from ._utils import (
    LOG_FILE_DEFAULT_DIRECTORY,
    _create_datestamp,
    _create_log_datetime_stamp,
)


class HandlerController:
    """
    Application-scoped singleton. Resolves paths and owns stdlib handlers.

    Use HandlerController._reset() in test teardown to allow re-initialisation.
    Do NOT call _reset() in production code.
    """

    # Class-level singleton state
    handlers: dict = {}
    log_datetime_stamp: str = ""
    run_directory: str = ""
    log_directory: str = ""
    json_file_path: str = ""
    readable_file_path: str = ""
    json_file_handler: Optional[logging.Handler] = None
    readable_file_handler: Optional[logging.FileHandler] = None
    stream_handler: Optional[logging.StreamHandler] = None
    mode: AbstractLoggingMode = DIRECTORY_PER_RUN
    _initialized: bool = False

    def __new__(
        cls,
        log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
        mode: AbstractLoggingMode = DIRECTORY_PER_RUN,
    ):
        if cls._initialized:
            raise RuntimeError(
                "HandlerController is already initialised. "
                "Call HandlerController._reset() before creating a new instance "
                "(test teardown only)."
            )

        cls.mode = mode
        cls.log_directory = log_directory

        # Resolve run directory and datetime stamp
        cls.log_datetime_stamp, cls.run_directory = cls._resolve_run_directory(
            log_directory, mode
        )

        # JSON file handler — read settings from mode
        if mode.json:
            cls.json_file_path, cls.json_file_handler = cls._create_json_handler(
                mode.json_level, mode
            )
        else:
            cls.json_file_path = ""
            cls.json_file_handler = None

        # Readable text file handler — read settings from mode
        if mode.file:
            cls.readable_file_path, cls.readable_file_handler = cls._create_readable_handler(
                mode.file_level
            )
        else:
            cls.readable_file_path = ""
            cls.readable_file_handler = None

        # Stream handler — read settings from mode
        cls.stream_handler = (
            cls._create_stream_handler(mode.stream_level) if mode.stream else None
        )

        cls._initialized = True
        return super().__new__(cls)

    # ------------------------------------------------------------------
    # Private factory methods
    # ------------------------------------------------------------------

    @classmethod
    def _resolve_run_directory(
        cls, log_directory: str, mode: AbstractLoggingMode
    ) -> Tuple[str, str]:
        """Return (log_datetime_stamp, run_directory) based on DirectoryLayout."""
        stamp = _create_log_datetime_stamp()
        layout = mode.directory_layout

        match layout:
            case DirectoryLayout.FLAT:
                run_dir = log_directory
            case DirectoryLayout.PER_RUN:
                daily = _create_datestamp()
                run_dir = os.path.join(log_directory, daily, stamp)
            case DirectoryLayout.DAILY:
                daily = _create_datestamp()
                run_dir = os.path.join(log_directory, daily)
            case DirectoryLayout.ROTATING:
                run_dir = log_directory
            case _:
                raise ValueError(f"Unknown DirectoryLayout: {layout}")

        os.makedirs(run_dir, exist_ok=True)
        return stamp, run_dir

    @classmethod
    def _create_json_handler(
        cls, json_level: int, mode: AbstractLoggingMode
    ) -> Tuple[str, logging.Handler]:
        """Create and return (path, handler) for the JSON log file."""
        if mode.directory_layout == DirectoryLayout.ROTATING:
            json_file_path = os.path.join(cls.run_directory, "loggers.json.log")
            handler = TimedRotatingFileHandler(
                filename=json_file_path,
                when="midnight",
                backupCount=30,
                encoding="utf-8",
            )
        else:
            json_file_path = os.path.join(
                cls.run_directory, f"{cls.log_datetime_stamp}.json.log"
            )
            handler = logging.FileHandler(json_file_path, encoding="utf-8")

        handler.setLevel(json_level)
        # Formatter is attached by configure_logging() after structlog is configured
        return json_file_path, handler

    @classmethod
    def _create_readable_handler(
        cls, file_level: int
    ) -> Tuple[str, logging.FileHandler]:
        """Create and return (path, handler) for the human-readable log file."""
        readable_file_path = os.path.join(
            cls.run_directory, f"{cls.log_datetime_stamp}_main.log"
        )
        handler = logging.FileHandler(readable_file_path, encoding="utf-8")
        handler.setLevel(file_level)
        # Formatter is attached by configure_logging()
        return readable_file_path, handler

    @classmethod
    def _create_stream_handler(cls, level: int) -> logging.StreamHandler:
        """Create and return a StreamHandler at the given level."""
        handler = logging.StreamHandler()
        handler.setLevel(level)
        # Formatter is attached by configure_logging()
        return handler

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def __init__(
        self,
        log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
        mode: AbstractLoggingMode = DIRECTORY_PER_RUN,
    ) -> None:
        pass  # All setup is done in __new__

    def handler_names(self) -> list[str]:
        """Return a list of active handler names (for test compatibility)."""
        names = []
        if self.json_file_handler is not None:
            names.append("json")
        if self.readable_file_handler is not None:
            names.append("main")
        if self.stream_handler is not None:
            names.append("stream")
        return names

    # ------------------------------------------------------------------
    # Test-only reset
    # ------------------------------------------------------------------

    @classmethod
    def _reset(cls) -> None:
        """
        Reset all class state. FOR TEST USE ONLY.

        Flushes and closes all handlers before clearing state.
        """
        for handler in [cls.json_file_handler, cls.readable_file_handler, cls.stream_handler]:
            if handler is not None:
                try:
                    handler.flush()
                    handler.close()
                except Exception:
                    pass

        cls.handlers = {}
        cls.log_datetime_stamp = ""
        cls.run_directory = ""
        cls.log_directory = ""
        cls.json_file_path = ""
        cls.readable_file_path = ""
        cls.json_file_handler = None
        cls.readable_file_handler = None
        cls.stream_handler = None
        cls.mode = DIRECTORY_PER_RUN
        cls._initialized = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.run_directory!r})"
