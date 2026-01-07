# Import specific functions or classes for direct access at a package level
from .logger import Logger
from .logger_configs import LoggingHandlerController, configure_logger
from .utils import ELoggingFormats, LOG_FILE_DEFAULT_DIRECTORY
from .utils import create_datestamp, create_timestamp, create_log_datetime_stamp, compose_global_run_id

# Define package-level variables
__version__ = '1.1.1'
__Author__ = 'Elias Rodkey'