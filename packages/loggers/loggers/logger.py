"""
logger.py

Class:
    Logger: a basic logging class for cleanly handling logging for a specific class or module
"""
import logging
import os
import shutil
from typing import Dict

from loggers.utils import ELoggingFormats, create_datestamp, create_log_datetime_stamp, compose_global_run_id



class Logger:
    """
    A logging class that uses singleton-like behavior to avoid creating duplicate loggers.
    Allows changing logging output location and level
    """

    # Initialize instances dictionary
    _instances: Dict = {}
    LOG_FILE_DEFAULT_DIRECTORY: str = os.path.join('data', 'logs')

    # Adds logging levels to Logger class so logging library doesn't have to imported every time Logger class is imported
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    WARN = logging.WARNING
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
            run_name (str): configuration or parameters unique to the specific run
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

        # sets minumum logging level for initialization
        instance.logger.setLevel(logging.DEBUG)

        # TODO: make the run name optional so it can be set at the top level and not set after the first instace is created
        # Set the global run ID only once
        if not hasattr(cls, '_run_id'):
            cls._run_id = create_log_datetime_stamp()

        cls._instances[name] = instance
        return instance


    def __init__(
            self, name: str,
            log_file_default_dir: str = LOG_FILE_DEFAULT_DIRECTORY
            ):
        """Initializes logger variables if it hasn't been initialized yet"""

        # Check if the instance has already been initialized to avoid re-initialization
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # Initialized instance variables
        self.handlers = {}
        self.name = name
        self.log_file_defaullt_dir = os.path.join(os.path.abspath(os.curdir), log_file_default_dir)

        # Create log file directory if it doesn't exist
        if not os.path.exists(self.log_file_defaullt_dir):
            os.makedirs(self.log_file_defaullt_dir)
        
        # Mark the instance as initialized to avoid re-initialization
        self._initialized = True


    @classmethod
    def set_run_name(cls, run_name: str) -> None:
        """
        Sets the run name for the Logger class

        Args:
            run_name (str): a name to help identify the run (configuration details or unique parameters)
        """
        cls._run_id = compose_global_run_id(run_name)


    @classmethod
    def _get_instances(cls) -> dict:
        """
        Retrives the other existing Logger instances from the class variable

        Returns:
            _instances dictionary 'logger_name': (Logger instance)
        """
        return cls._instances
    

    @classmethod
    def _list_logger_names(cls) -> list:
        """
        Retrieves a list of the existing logger names

        Returns:
            list[str] logger names
        """
        return cls._get_instances().keys()


    @classmethod
    def _get_run_id(cls) -> str:
        """
        Retrieves the run ID for the Logger class

        Returns:
            str
        """
        return cls._run_id
    

    @classmethod
    def _del_logger(cls, name: str) -> None:
        """
        Deletes a logger instance from the _instances dictionary

        Args:
            name (str): the name of the logger to be deleted
        """
        if name in cls._instances.keys():
            logger = cls._instances[name]

            # Properly remove and close all handlers
            for handler in list(logger.logger.handlers):  # Use list() to avoid modifying the list while iterating
                logger.logger.removeHandler(handler)  # Detach the handler from the logger

            del cls._instances[name]
    

    @property
    def run_id(self) -> str:
        """
        Retrieves the run ID for the Logger class

        Returns:
            str
        """
        return self._get_run_id()


    def get_logger(self):
        """Retrives the new logger instance"""
        return self.logger


    def add_console_handler(
            self, name: str,
            level = logging.INFO, 
            format = ELoggingFormats.FORMAT_BASIC
            ) -> None:
        """
        Creates a console log handler for the current logger instance

        Args:
            name (str): a name for the new handler
            level: logging display level
            format (str): logging message display format
        """

        # Checks if a handler of the same name already exists to avoid accidental overwritting
        if self._handler_exists(name):
            self.logger.warn(f'Handler with name {name} already exists in logger {self.name}')
            return
        
        # Configure console hander with given format and logging level
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(format))
        console_handler.setLevel(level)

        # Adds console handler to the handlers dict and the logger
        self.handlers[name] = console_handler
        self.logger.addHandler(console_handler)
    
    
    def add_file_handler(
            self, handler_name: str = 'main',
            level = logging.INFO, 
            format = ELoggingFormats.FORMAT_BASIC,
            ) -> None:
        """
        Creates a file log handler for the current logger instance

        Args:
            handler_name (str): a name for the new handler
            level: logging display level
            format (str): logging message display format
        """
        
        # Checks if a handler of the same name already exists to avoid accidental overwritting
        if self._handler_exists(handler_name):
            self.logger.warn(f'Handler with name {handler_name} already exists in logger {self.name}')
            return

        # Create the full name of the file, datetime stamp + run name + handler name
        full_filename = f'{self.run_id}_{handler_name}.log'

        # Generate new directory for log file to be stored and create the full file path
        run_id_dir = self._create_run_id_dir()
        file_path = os.path.join(run_id_dir, full_filename)

        # Configure console hander with given format and logging level
        file_handler = logging.FileHandler(filename = file_path, mode = 'a', encoding = 'utf-8')
        file_handler.setFormatter(logging.Formatter(format))
        file_handler.setLevel(level)

        # Adds console handler to the handlers dict and the logger
        self.handlers[handler_name] = file_handler
        self.logger.addHandler(file_handler)
        self.debug(f'File handler {handler_name} added to logger {self.name} with path: {file_path}')


    def join_handler(self, logger_name: str, handler_name: str) -> None:
        """
        Adds the handler of an existing logger to this instance for shared output

        Args:
            logger_name (str): the name of the Logger instance
            handler_name (str): the name of the handler to be added (from when the handler is created)
        """

        # Retrieve the target handler
        logger_instance = self._get_instances()[logger_name]
        handler = logger_instance.handlers[handler_name]

        # Add the handler to the current instance
        self.handlers[handler_name] = handler
        self.logger.addHandler(handler)

    
    def remove_handler(self, handler_name: str) -> None:
        """
        Removes a handler from the current logger instance

        Args:
            handler_name (str): the name of the handler to be removed
        """

        # Check if the handler exists in the current instance
        if self._handler_exists(handler_name):
            # Remove the handler from the logger and handlers dict
            self.logger.removeHandler(self.handlers[handler_name])
            del self.handlers[handler_name]
        else:
            self.logger.warning(f'remove_handler error: Handler {handler_name} does not exist in logger {self.name}')


    def clear_todays_logs(self) -> None:
        """
        Clears all the logs in the current log directory for today
        """
        # Check if the directory exists
        if os.path.exists(self.date_dir):
            # deletes todays log directory and all files in it
            shutil.rmtree(self.date_dir)


    def clear_all_logs(self) -> None:
        """
        Clears all the logs in the current log directory
        """
        # Check if the directory exists
        if os.path.exists(self.log_file_defaullt_dir):
            # Remove all files in the data/logs directory
            for directory in os.listdir(self.log_file_defaullt_dir):
                directory_path = os.path.join(self.log_file_defaullt_dir, directory)
                if os.path.isdir(directory_path):
                    shutil.rmtree(directory_path)
                else:
                    os.remove(directory_path)
            

    def _create_todays_log_dir(self) -> bool:
        """
        Creates a directory in the default logs directory with todays date if it doesn't exist
        
        Returns:
            str: the path to todays log directory
        """

        # Create a path to the new log directory
        date_stamp = create_datestamp()
        self.date_dir = os.path.join(self.log_file_defaullt_dir, date_stamp)
        
        # If the path doesn't exists create the new directory
        if not os.path.exists(self.date_dir):
            os.makedirs(self.date_dir)
        
        return self.date_dir
    

    def _create_run_id_dir(self) -> None:
        """
        Creates a new directory for the specific run of the program

        Returns:
            str: the path to todays log directory
        """

        # Create a path to the new run ID directory
        date_path = self._create_todays_log_dir()
        self.run_dir = os.path.join(date_path, self.run_id)

        # If the path doesn't exists create the new directory
        if not os.path.exists(self.run_dir):
            os.makedirs(self.run_dir)
        
        return self.run_dir
    

    def _handler_exists(self, handler_name: str) -> bool:
        """
        Checks if the a handler with the given name already exists

        Args:
            handler_name (str): the name of a handler to be checked in self.handlers
        """
        return handler_name in self._list_handlers()


    def _list_handlers(self) -> list:
        """
        Creates a list of the names of all handlers

        Returns:
            list[str] handler names
        """
        return self.handlers.keys()


    def debug(self, message: str) -> None:
        """
        Logs a debug message

        Args:
            message (str): the message to be logged
        """
        self.logger.debug(message)


    def info(self, message: str) -> None:
        """
        Logs a info message

        Args:
            message (str): the message to be logged
        """
        self.logger.info(message)


    def warn(self, message: str) -> None:
        """
        Logs a warning message

        Args:
            message (str): the message to be logged
        """
        self.logger.warning(message)


    def warning(self, message: str) -> None:
        """
        Logs a warning message

        Args:
            message (str): the message to be logged
        """
        self.logger.warning(message)


    def error(self, message: str) -> None:
        """
        Logs a error message

        Args:
            message (str): the message to be logged
        """
        self.logger.error(message)
    

    def critical(self, message: str) -> None:
        """
        Logs a ctritical message

        Args:
            message (str): the message to be logged
        """
        self.logger.critical(message)


if __name__ == "__main__":

    test_logger = Logger("test")
    main_logger = Logger("main")

    # test file handler functions
    test_logger.add_file_handler('file_1', level=logging.DEBUG)
    main_logger.add_file_handler('file_1', level=logging.DEBUG)

    log_file_path = os.path.join(test_logger.run_dir, f'{test_logger.run_id}_file_1.log')

    test_logger.debug('debug message')
    test_logger.info('info message')
    test_logger.warning('warning message')

    with open(log_file_path, "r") as log_file:
            logs = log_file.read()
            print(logs)

    test_logger.remove_handler('file_1')

    test_logger.debug('debug message')
    test_logger.info('info message')
    test_logger.warning('warning message')

    with open(log_file_path, "r") as log_file:
            logs = log_file.read()
            print(logs)

    main_logger.debug(Logger._instances)
    Logger._del_logger("test")
    main_logger.debug(Logger._instances)
    