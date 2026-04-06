"""
pleasant_loggers._modes

Logging mode type hierarchy: DirectoryLayout enum, AbstractLoggingMode ABC,
LoggingMode concrete dataclass, and five built-in mode instances.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging


class DirectoryLayout(str, Enum):
    """Determines how log files are organised on disk."""
    FLAT = "flat"
    DAILY = "daily"
    PER_RUN = "per_run"
    ROTATING = "rotating"


@dataclass
class AbstractLoggingMode(ABC):
    """Abstract base for all logging mode configurations."""
    stream: bool
    stream_level: int
    file: bool
    file_level: int
    json: bool
    json_level: int
    directory_layout: DirectoryLayout

    @abstractmethod
    def validate(self) -> None:
        """Raise ValueError if the mode configuration is self-contradictory."""
        ...


@dataclass
class LoggingMode(AbstractLoggingMode):
    """Concrete logging mode. At least one output handler must be enabled."""

    def validate(self) -> None:
        if not self.stream and not self.file and not self.json:
            raise ValueError(
                "LoggingMode must enable at least one output handler "
                "(stream, file, or json)."
            )


# ---------------------------------------------------------------------------
# Five built-in mode instances
# ---------------------------------------------------------------------------

BASIC_SINGLE_FILE = LoggingMode(
    stream=True,
    stream_level=logging.INFO,
    file=True,
    file_level=logging.DEBUG,
    json=False,
    json_level=logging.DEBUG,
    directory_layout=DirectoryLayout.FLAT,
)

BASIC_JSON_FILE = LoggingMode(
    stream=True,
    stream_level=logging.INFO,
    file=False,
    file_level=logging.DEBUG,
    json=True,
    json_level=logging.DEBUG,
    directory_layout=DirectoryLayout.FLAT,
)

DIRECTORY_PER_RUN = LoggingMode(
    stream=True,
    stream_level=logging.INFO,
    file=True,
    file_level=logging.INFO,
    json=True,
    json_level=logging.DEBUG,
    directory_layout=DirectoryLayout.PER_RUN,
)

DAILY_DIRECTORY = LoggingMode(
    stream=False,
    stream_level=logging.INFO,
    file=True,
    file_level=logging.DEBUG,
    json=True,
    json_level=logging.DEBUG,
    directory_layout=DirectoryLayout.DAILY,
)

BASIC_ROTATING_HANDLER = LoggingMode(
    stream=True,
    stream_level=logging.WARNING,
    file=True,
    file_level=logging.DEBUG,
    json=True,
    json_level=logging.DEBUG,
    directory_layout=DirectoryLayout.ROTATING,
)
