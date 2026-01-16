"""
test_loggers.py

Unit tests for logger.py using pytest.
"""
import sys
sys.path.insert(0, ".")

import pytest
import time
import os

from loggers.logger import Logger
from loggers.utils import ELoggingFormats as ELF


# Global Variables
TEST_LOGGER_NAME_1 = "test_1"
TEST_LOGGER_NAME_2 = "test_2"
TEST_LOGGER_NAME_3 = "test_3"
RUN_NAME = "unittest"


# Test Class for Logger
class TestLogger:
    """Unit tests for Logger."""


    def test_del_logger(self):
        """Test if logger is deleted."""
        logger_1 = Logger(TEST_LOGGER_NAME_1)
        logger_2 = Logger(TEST_LOGGER_NAME_2)

        assert Logger._instances[TEST_LOGGER_NAME_1] == logger_1
        assert Logger._instances[TEST_LOGGER_NAME_2] == logger_2

        # Delete the first loggers
        Logger._del_logger(TEST_LOGGER_NAME_1)

        assert TEST_LOGGER_NAME_1 not in Logger._instances.keys()
        assert Logger._instances[TEST_LOGGER_NAME_2] == logger_2

        # Delete the second loggers
        Logger._del_logger(TEST_LOGGER_NAME_2)

        # Check the logger have been deleted
        assert TEST_LOGGER_NAME_1 not in Logger._instances.keys()
        assert TEST_LOGGER_NAME_2 not in Logger._instances.keys()


    def test_singleton_like(self):
        """Test if Logger singleton like"""
        logger_1 = Logger(TEST_LOGGER_NAME_1)
        logger_2 = Logger(TEST_LOGGER_NAME_1)
        logger_3 = Logger(TEST_LOGGER_NAME_1)

        assert logger_1.logger == logger_2.logger
        assert logger_2.logger == logger_3.logger
        assert logger_3.logger == logger_1.logger

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)
        Logger._del_logger(TEST_LOGGER_NAME_2)
        Logger._del_logger(TEST_LOGGER_NAME_3)


    def test_run_id_integrity(self):
        """Test the run_id property persists between instances."""
        logger_1 = Logger(TEST_LOGGER_NAME_1)
        time.sleep(1)
        logger_2 = Logger(TEST_LOGGER_NAME_2)

        assert logger_1.run_id == logger_2.run_id

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)
        Logger._del_logger(TEST_LOGGER_NAME_2)


    def test_create_log_dir(self):
        """Test the creation of the log directory."""
        Logger(TEST_LOGGER_NAME_1)
        Logger(TEST_LOGGER_NAME_2, log_file_default_dir="logs")
        
        assert os.path.exists(os.path.join(os.curdir, "data\\logs"))
        assert os.path.exists(os.path.join(os.curdir, "logs"))

        # Remove non-standard log directory
        os.rmdir(os.path.join(os.curdir, "logs"))

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)
        Logger._del_logger(TEST_LOGGER_NAME_2)


    def test_handler_exists(self):
        """Test if handler exists check exists"""
        logger = Logger(TEST_LOGGER_NAME_1)
        logger.add_console_handler("console")

        assert logger._handler_exists("console")
        assert "console" in logger._list_handlers()

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)



    def test_add_file_handler(self):
        """Test adding a file handler."""
        # Create a logger instance
        logger = Logger(TEST_LOGGER_NAME_1)
        
        # Add a file handler with a specific name and level
        logger.add_file_handler("file_1", level=Logger.DEBUG)

        # See if the file was created correctly
        assert os.path.exists(os.path.join(logger.run_dir, f"{logger.run_id}_file_1.log"))

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)


    def test_remove_handler(self):
        """Test removing a handler."""
        # Create a logger instance
        logger = Logger(TEST_LOGGER_NAME_1)
        
        # Add a file handler with a specific name and level
        logger.add_file_handler("file_1", level=Logger.DEBUG)

        assert logger._handler_exists("file_1")

        # Remove  file handler with a specific name (already created in previous test)
        logger.remove_handler("file_1")

        # Check if the handler was removed
        assert not logger._handler_exists("file_1")

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)
    

    def test_multiple_file_handlers(self):
        """Test adding multiple file handlers to the same Logger instance."""
        # Create a logger instance
        logger = Logger(TEST_LOGGER_NAME_1)
        
        # Add a file handler with a specific name and level
        logger.add_file_handler("file_1", level=Logger.DEBUG)
        logger.add_file_handler("file_2", level=Logger.WARNING)
        
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")

        log_file_path_1 = os.path.join(logger.run_dir, f"{logger.run_id}_file_1.log")
        log_file_path_2 = os.path.join(logger.run_dir, f"{logger.run_id}_file_2.log")


        with open(log_file_path_1, "r") as log_file:
            logs = log_file.read()
            assert "DEBUG" in logs
            assert "INFO" in logs
            assert "WARNING" in logs
            assert "ERROR" in logs
            assert "CRITICAL" in logs


        with open(log_file_path_2, "r") as log_file:
            logs = log_file.read()
            assert "DEBUG" not in logs
            assert "INFO" not in logs
            assert "WARNING" in logs
            assert "ERROR" in logs
            assert "CRITICAL" in logs

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)


    def test_join_file_handlers(self):
        """Test joining file handlers."""
        # Create a logger instance
        logger_1 = Logger(TEST_LOGGER_NAME_1)
        logger_2 = Logger(TEST_LOGGER_NAME_2)
        
        # Add a file handler with a specific name and level
        logger_1.add_file_handler("file_1", level=Logger.DEBUG, format=ELF.FORMAT_LOGGER_NAME)
        logger_2.join_handler(TEST_LOGGER_NAME_1, "file_1")

        # Add debug messages to
        logger_1.debug("debug message")
        logger_1.info("info message")
        logger_2.warning("warning message")
        logger_2.error("error message")
        
        # Check if the handlers were joined correctly
        log_file_path = os.path.join(logger_1.run_dir, f"{logger_1.run_id}_file_1.log")

        with open(log_file_path, "r") as log_file:
            logs = log_file.read()
            assert f"{TEST_LOGGER_NAME_1} - DEBUG" in logs
            assert f"{TEST_LOGGER_NAME_1} - INFO" in logs
            assert f"{TEST_LOGGER_NAME_2} - WARNING" in logs
            assert f"{TEST_LOGGER_NAME_2} - ERROR" in logs

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)
        Logger._del_logger(TEST_LOGGER_NAME_2)
    

    def test_clear_todays_logs(self):
        """Test clearing todays logs."""
        # Create a logger instance
        logger = Logger(TEST_LOGGER_NAME_1)

        # Create todays log directory if it doesn"t exist
        logger._create_todays_log_dir()

        assert os.path.exists(logger.date_dir)
        
        # Clear the logs
        logger.clear_todays_logs()

        assert not os.path.exists(logger.date_dir)

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)

    
    def test_clear_all_logs(self):
        """Test clearing todays logs."""
        # Create a logger instance
        logger = Logger(TEST_LOGGER_NAME_1)

        # Create todays log directory if it doesn"t exist
        logger._create_todays_log_dir()

        contents = os.listdir(logger.log_file_defaullt_dir)

        assert contents != []
        
        # Clear the logs
        logger.clear_all_logs()

        contents = os.listdir(logger.log_file_defaullt_dir)

        assert contents == []

        # Delete loggers after test
        Logger._del_logger(TEST_LOGGER_NAME_1)