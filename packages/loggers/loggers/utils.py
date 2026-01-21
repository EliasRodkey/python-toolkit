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
    get_log_directories: Returns a list of the direcotry names inside of the default log directory.
    get_log_files:Returns a dictionary with the daily log folders as keys and a list of all of the log file names in the log directory as values.
    delete_log_directory: Deletes the directory and all contained files at the given directory name inside the default log direcotry
    delete_todays_logs: Deletes the directory that contains todays logs
    clear_logs: Deletes all log directories and files in the default log directory
"""

from datetime import datetime, timedelta
from enum import Enum
import logging
import os
import shutil

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


def get_log_directories(default_log_directory: str=LOG_FILE_DEFAULT_DIRECTORY) -> list[str]:
    """Returns a list of the direcotry names inside of the default log directory."""
    contents = os.listdir(default_log_directory)

    return [dir for dir in contents if not os.path.isdir(dir)]


def get_log_files(default_log_directory: str=LOG_FILE_DEFAULT_DIRECTORY) -> dict[str, list[str]]:
    """
    Returns a dictionary with the daily log folders as keys 
    and a list of all of the log file names in the log directory as values.
    """
    log_file_dict = {}
    log_dirs = get_log_directories(default_log_directory)

    # Loop over all directories in the root log directory
    for dir in log_dirs:
        current_log_dir = os.path.join(default_log_directory, dir)
        contents = os.listdir(current_log_dir)

        # Assign list of log file names to daily timestamp
        log_file_dict[dir] = [file for file in contents if file.endswith(".log")]
    
    return log_file_dict


def delete_log_directory(directory_name: str, default_log_directory: str=LOG_FILE_DEFAULT_DIRECTORY) -> None:
    """Deletes the directory and all contained files at the given directory name inside the default log direcotry"""
    path = os.path.join(os.getcwd(), default_log_directory, directory_name)
    if os.path.exists(path):
        shutil.rmtree(path)


def delete_todays_logs(default_log_directory: str=LOG_FILE_DEFAULT_DIRECTORY) -> None:
    """Deletes the directory that contains todays logs"""
    todays_log_dir_name = create_datestamp()
    delete_log_directory(todays_log_dir_name, default_log_directory=default_log_directory)


def clear_logs(default_log_directory: str=LOG_FILE_DEFAULT_DIRECTORY) -> None:
    """Deletes all log directories and files in the default log directory"""
    log_dirs = get_log_directories(default_log_directory)
    for dir in log_dirs:
        delete_log_directory(dir, default_log_directory=default_log_directory)


def add_performance_level():
    """
    Custom performance logging level for measuring the time different program actions take.
    Adds the performance metrics to the extra dict kwarg as 'time_stamp' and 'performance'.
    Interesting note, any time this function is called, the module will list "utils" instead of the calling module.
    """
    # Add performance level name to logging library
    logging.addLevelName(PERFORMANCE_LEVEL_NUM, "PERFORMANCE")

    # Define performance logging function
    def performance(self, message, *args, **kwargs):
        if self.isEnabledFor(PERFORMANCE_LEVEL_NUM):
            stacklevel = kwargs.pop("stacklevel", 1)
            self._log(
                PERFORMANCE_LEVEL_NUM,
                message,
                args,
                stacklevel=stacklevel + 1,
                **kwargs,
            )

    # Set performance function to rool logger class
    logging.Logger.performance = performance