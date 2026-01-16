"""
loggers.utils.py

A python module which contains generic functions related to the logger and super_logger classes

Class:
    ELoggingFormats: an Enum class which stores different formatting strings for logger formatting

Functions:
    create_datestamp: generates todays date as a string
    create_timestamp: generates the current time as a string
    create_log_datetime_stamp: combines the date and timestamp for a unique file identifier
    compose_global_run_id: creates an id unique to the program run based on the datetime stamp and a run ID   
    # NOTE: Not implemented
    # get_log_directories:
    # get_log_files:
    # clear_daily_logs:
    # clear_logs:
"""

from datetime import datetime
from enum import Enum
import os

# Default directory to store log files
LOG_FILE_DEFAULT_DIRECTORY: str = os.path.join("data", "logs")
PERFORMANCE_LEVEL_NUM = 15



class ELoggingFormats(str, Enum):
    """
    Contains different format strings for logging output
    """
    ASCTIME = "%(asctime)s"
    MODULE = "%(module)s"
    MODULE_BRACKETS = "[%(module)s]"
    FUNC_NAME = "%(funcName)s"
    FUNC_NAME_BRACKETS = "[%(funcName)s]"
    LOG_LEVEL = "%(levelname)s"
    LOG_LEVEL_BRACKETS = "[%(levelname)s]"
    LINE_NO = "%(lineno)d"
    LINE_NO_BRACKETS = "[%(lineno)d]"
    LOGGER_NAME = "%(name)s"
    LOGGER_NAME_BRACKETS = "[%(name)s]"
    MESSAGE = "%(message)s"

    FORMAT_BASIC = f"{ASCTIME} - {LOGGER_NAME} - {LOG_LEVEL} - {MESSAGE}"
    FORMAT_LOGGER_NAME = f"{ASCTIME} - {LOGGER_NAME} - {LOG_LEVEL} - {MESSAGE}"
    FORMAT_LOGGER_NAME_BRACKETS = f"{ASCTIME} - {LOGGER_NAME_BRACKETS}{LOG_LEVEL_BRACKETS}: {MESSAGE}"
    FORMAT_FUNC_NAME = f"{ASCTIME} {LOG_LEVEL_BRACKETS}{FUNC_NAME_BRACKETS}: {MESSAGE}"
    FORMAT_MODULE_FUNC_NAME = f"{ASCTIME} {LOG_LEVEL_BRACKETS}{MODULE_BRACKETS}{FUNC_NAME_BRACKETS}: {MESSAGE}"

    def __str__(self):
        return str(self.value)



def create_datestamp() -> str:
    """
    Creates a string of the current datetime YYYY-MM-DD

    Returns:
        the current days date as a string    
    """
    return datetime.now().strftime("%Y-%m-%d")


def create_timestamp() -> str:
    """
    Creates a string of the current time HHMMSS
    
    Returns:
        the current time as a string    
    """
    return datetime.now().strftime("%H%M%S")


def create_log_datetime_stamp() -> str:
    """
    Uses current datetime and program run id to create a datetime stamp for log file

    Returns:
        str: a log filename datetime stamp
    """
    return f"{create_datestamp()}_{create_timestamp()}"


def compose_global_run_id(run_name: str) -> str:
    """
    Creates an ID for the current run of the program to be used across loggers

    Args:
        run_name (str): a name to help identify the run (configuration details or unique parameters)
    """
    time_id = create_log_datetime_stamp()
    return f"{time_id}_{run_name}"


def get_log_directories(log_direcotry: str=LOG_FILE_DEFAULT_DIRECTORY) -> list[str]:
    """Returns a list of the direcotry names inside of the default log directory."""
    contents = os.listdir(log_direcotry)

    return [dir for dir in contents if not os.path.isdir(dir)]

def get_log_files(log_directory: str=LOG_FILE_DEFAULT_DIRECTORY) -> list[str]:
    """"""