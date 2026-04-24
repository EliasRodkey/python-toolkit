"""
pleasant_loggers._config

configure_logging() — the primary entry point for setting up pleasant_loggers.

Wires structlog's processor chain to stdlib handlers via ProcessorFormatter,
creates a HandlerController singleton, and configures the root logger.
"""
import dataclasses
import logging
import sys
from typing import Optional

import structlog
from structlog.stdlib import ProcessorFormatter

from pleasant_loggers._handlers import HandlerController
from pleasant_loggers._modes import (
    AbstractLoggingMode,
    BASIC_SINGLE_FILE,
)
from pleasant_loggers._processors import build_shared_processor_chain
from ._utils import LOG_FILE_DEFAULT_DIRECTORY


def configure_logging(
    log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
    mode: AbstractLoggingMode = BASIC_SINGLE_FILE,
    stream: Optional[bool] = None,
    stream_level: Optional[int] = None,
    file: Optional[bool] = None,
    file_level: Optional[int] = None,
    json: Optional[bool] = None,
    json_level: Optional[int] = None,
) -> HandlerController:
    """
    Configure the root logger and structlog processor chain.

    Args:
        log_directory: Parent folder for all log files. Defaults to data/logs/.
        mode: A LoggingMode (or AbstractLoggingMode subclass) that provides all
              handler defaults. Use one of the five built-in instances or construct
              your own.
        stream: Override mode.stream (whether to add a StreamHandler).
        stream_level: Override mode.stream_level.
        file: Override mode.file (whether to add a readable text file handler).
        file_level: Override mode.file_level.
        json: Override mode.json (whether to add a JSON file handler).
        json_level: Override mode.json_level.

    Returns:
        HandlerController: Owns all handlers and exposes file paths.

    Raises:
        RuntimeError: If configure_logging() has already been called.
        ValueError: If the resolved mode configuration is invalid.
    """
    if HandlerController._initialized:
        raise RuntimeError(
            "configure_logging() has already been called. "
            "Call HandlerController._reset() before reconfiguring "
            "(test teardown only)."
        )

    # Apply fine-grained overrides via dataclasses.replace — never mutates
    # the built-in mode instances.
    overrides = {
        k: v for k, v in {
            "stream": stream,
            "stream_level": stream_level,
            "file": file,
            "file_level": file_level,
            "json": json,
            "json_level": json_level,
        }.items()
        if v is not None
    }
    resolved_mode = dataclasses.replace(mode, **overrides) if overrides else mode
    resolved_mode.validate()

    # ------------------------------------------------------------------
    # Configure structlog
    # ------------------------------------------------------------------
    shared_processors = build_shared_processor_chain()

    structlog.configure(
        processors=shared_processors + [
            # When a stdlib logger goes through ProcessorFormatter it already
            # has the terminal renderer applied — this final step is a pass-through.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # ------------------------------------------------------------------
    # Build per-handler ProcessorFormatters
    # ------------------------------------------------------------------
    json_formatter = ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    no_color_formatter = ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=False),
        ],
    )

    console_formatter = ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
    )

    # ------------------------------------------------------------------
    # Create HandlerController (resolves paths, creates raw handlers)
    # ------------------------------------------------------------------
    controller = HandlerController(log_directory=log_directory, mode=resolved_mode)

    # Attach formatters to handlers
    if controller.json_file_handler is not None:
        controller.json_file_handler.setFormatter(json_formatter)

    if controller.readable_file_handler is not None:
        controller.readable_file_handler.setFormatter(no_color_formatter)

    if controller.stream_handler is not None:
        controller.stream_handler.setFormatter(console_formatter)

    # ------------------------------------------------------------------
    # Configure the root logger
    # ------------------------------------------------------------------
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if controller.json_file_handler is not None:
        root_logger.addHandler(controller.json_file_handler)
    if controller.readable_file_handler is not None:
        root_logger.addHandler(controller.readable_file_handler)
    if controller.stream_handler is not None:
        root_logger.addHandler(controller.stream_handler)

    return controller
