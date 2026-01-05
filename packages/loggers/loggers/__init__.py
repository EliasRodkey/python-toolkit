# Import specific functions or classes for direct access at a package level
from .logger import Logger
from .utils import ELoggingFormats
from .utils import create_datestamp, create_timestamp, create_log_datetime_stamp, compose_global_run_id

# Define package-level variables
__version__ = '1.1.0'
__Author__ = 'Elias Rodkey'