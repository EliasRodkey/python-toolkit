# Import specific functions or classes for direct access at a package level
from configure_logging import configure_logging
from .handler_controller import HandlerController, StructuredLogger
from .json_log_parser import JSONLogParser, LogRecord
from .utils import ELoggingFormats, LOG_FILE_DEFAULT_DIRECTORY, add_performance_level
from .utils import create_datestamp, create_timestamp, create_log_datetime_stamp, compose_global_run_id
from .utils import get_log_directories, get_log_files, delete_log_directory, delete_todays_logs, clear_logs

# Set default logger to structured logger
import logging
logging.setLoggerClass(StructuredLogger)

# Define package-level variables
__version__ = "1.3.0"
__Author__ = "Elias Rodkey"