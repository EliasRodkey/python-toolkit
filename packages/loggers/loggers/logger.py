"""
logger.py

Class:
    Logger: a basic logging class for cleanly handling logging for a specific class or module
"""
import logging
from typing import List, Dict, Union

from common import ELoggingFormats

class Logger:
    """
    A logging class that uses singleton-like behavior to avoid creating duplicate loggers.
    Allows changing logging output location and level
    """

    # Initialize instances dictionary
    _instances = {}
    LOG_FILE_DEFAULT_DIRECTORY: str = 'docs\logs'

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARN
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


    def __new__(
            cls, name: str,
            log_file_default_dir: str = LOG_FILE_DEFAULT_DIRECTORY,
            ):
        """
        creates memory for the new object before __init__() is called. used in this case to control instance creation

        Args:
            cls: refers to the class itself, always an argument in the __new__ method for classes
                (like self for __init__ method)  
            name (str): the name of the logger instance being created, will be added to _instances{}
            log_file_default_dir : default relative location for log files to be generated 
        
        Returns:
            None
        """

        # Checks if the logger name already exists in the _instances dictionary
        # If the name exists it retrieves the logger that is already created
        if name in cls._instances:
            return cls._instances[name]
        
        # Calls the default __new__ method to create a new instance of the class
        instance = super(Logger, cls).__new__(cls)

        # Retrieves or creates a names logger instance
        instance.logger = logging.getLogger(name)

        cls._instances[name] = instance
        return instance


    def __init__(
            self, name: str,
            log_file_default_dir: str = LOG_FILE_DEFAULT_DIRECTORY
            ):
        # Initialize instance level variables
        self.name = name
        self.log_file_defaullt_dir = log_file_default_dir


    def get_logger(self):
        """Retrives the new logger instance"""
        return self.logger


    def add_console_handler(
            self, level = logging.INFO, 
            format = ELoggingFormats.FORMAT_BASIC
            ) -> None:
        """
        Creates a console log handler for the current logger instance

        Args:
            level: logging display level
            format (str): logging message display format
        
        Returns:
            None
        """
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(format))
        console_handler.setLevel(level)
        self.logger.addHandler(console_handler)
        

    
    def add_file_handler(
            self, level = logging.INFO, 
            format = ELoggingFormats.FORMAT_BASIC
            ) -> None:
        """
        Creates a file log handler for the current logger instance

        Args:
            level: logging display level
            format (str): logging message display format
        
        Returns:
            None
        """
        # TODO: automatically create path / dir to new log file
        file_name = ''
        file_handler = logging.FileHandler(filename = file_name, mode = 'w', encoding = 'utf-8')
        file_handler.setFormatter(logging.Formatter(format))
        file_handler.setLevel(level)
        self.logger.addHandler(file_handler)


if __name__ == "__main__":

    test_instance = Logger("test", level = logging.DEBUG)
    main_instance = Logger("main", logging_format=ELoggingFormats.FORMAT_LOGGER_NAME_BRACKETS)

    test_logger = test_instance.get_logger()
    main_logger = main_instance.get_logger()

    test_logger.debug('this is the test logger')
    main_logger.info('this is the main logger')