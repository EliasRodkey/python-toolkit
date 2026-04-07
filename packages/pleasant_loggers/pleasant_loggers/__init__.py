# Configuration
from ._config import configure_logging
from ._handlers import HandlerController

# Modes
from ._modes import (
    LoggingMode,
    AbstractLoggingMode,
    DirectoryLayout,
    BASIC_SINGLE_FILE,
    BASIC_JSON_FILE,
    DIRECTORY_PER_RUN,
    DAILY_DIRECTORY,
    BASIC_ROTATING_HANDLER,
)

# Levels
from ._levels import add_performance_level

# Logger entry point
from ._loggers import get_logger

# Analysis (pandas loaded lazily inside LogReader)
from ._analysis import LogReader

# Utilities
from ._utils import (
    get_log_directories,
    get_log_files,
    delete_log_directory,
    delete_todays_logs,
    clear_logs,
    LOG_FILE_DEFAULT_DIRECTORY,
)

__version__ = "2.0.0"
__author__ = "Elias Rodkey"
