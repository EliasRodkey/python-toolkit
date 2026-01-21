"""
loggers.tests.test_logger_configs.py

Unit test for logger_configs.py using pytest
"""

import json
import logging
import pytest
import os

from loggers.logger_configs import configure_logger
from loggers.utils import clear_logs, add_performance_level

add_performance_level()


@pytest.fixture()
def test_json_logs():
    """Fixture to create fresh log file structure before each test"""
    
    try:
        # Setup: create log folders and files and configure logger, register log messages
        logger = logging.getLogger(__name__)
        log_controller = configure_logger(logger)

        logger.debug("Something is happening behind the scenes...")
        logger.info("This message contains some extra information", extra={"var_1" : True, "var_2" : "ERROR"})
        logger.performance("FUNCTION PERFORMANCE")
        logger.warning("Oopsy daisy! don't do that again :(")
        logger.error("ERROR skjdbvwibuyfi8whf209[3r8h9weuvb]")
        logger.critical("SHUTTING DOWN BEEP BOOP")
        try:
            new_num = 6 / 0
        except Exception as e:
            logger.exception("Failed tricky thingy!", extra={"func_status": "FAIL"})

        yield logger, log_controller

    except Exception as e:
        print(e)
        raise

    finally:
        # Teardown: Ensure the session is closed and the files are deleted
        # pass
        log_controller.handlers["json"].flush()
        log_controller.handlers["json"].close()
        logger.removeHandler(log_controller.handlers["json"])

        log_controller.handlers["stream"].flush()
        log_controller.handlers["stream"].close()
        logger.removeHandler(log_controller.handlers["stream"])

        for name, handler in log_controller.handlers["readable"].items():
            handler.flush()
            handler.close()
            logger.removeHandler(handler)

        clear_logs()


class TestLoggingHandlerControler:
    """Test class from LoggingHandlerController"""

    def test_json_log_file_creation(self, test_json_logs):
        """Makes sure the JSON log file is created and formatted correctly"""
        logger, log_controller = test_json_logs
        assert os.path.exists(log_controller.json_file_path)

        with open(log_controller.json_file_path, "r") as file:
            data = [json.loads(line) for line in file if line.strip()]

        assert len(data) == 7, "Missing log entries"
        
        for entry in data:
            assert "timestamp" in entry, "missing log entry info"
            assert "level" in entry, "missing log entry info"
            assert "logger" in entry, "missing log entry info"
            assert "message" in entry, "missing log entry info"
            assert "module" in entry, "missing log entry info"
            assert "function" in entry, "missing log entry info"
            assert "line" in entry, "missing log entry info"
            assert "exception" in entry, "missing log entry info"
            assert "extra" in entry, "missing log entry info"
    

    def test_readable_log_file_creation(self, test_json_logs):
        """Makes sure the readable log file is created"""
        logger, log_controller = test_json_logs
        assert os.path.exists(log_controller.readable_file_path)

    
    def test_add_new_run_name_logger(self, test_json_logs):
        """Adds a new logger and run name. Should create a new readable log file and log messages should also go to existing json file"""
        logger, log_controller = test_json_logs

        # Create and configure a new logger with a different run name
        logger_2 = logging.getLogger("test_logger_2")
        log_controller_2 = configure_logger(logger_2, run_name="thread_2")

        logger_2.debug("Debug message")
        logger_2.performance("Thread 2 performance information", extra={"step": "time delta"})
        logger_2.info("Info message")
        logger_2.warning("Warning message")
        logger_2.error("Error message")
        logger_2.critical("Critical!!!")

        # Check that the new readable log file was created and is accessible from the original log controller obj
        readable_file_path_2 = log_controller_2.readable_file_path
        assert os.path.exists(readable_file_path_2)
        assert readable_file_path_2 == log_controller._run_names["thread_2"]["path"]

        # Ensure logs from logger_2 are not in logger readable log file
        with open(log_controller.readable_file_path, "r") as file:
            readable_data = [line for line in file if line.strip()]
        for line in readable_data:
            assert "thread_2" not in line

        # Ensure logs from original logger are not in logger_2 readable log file
        with open(readable_file_path_2, "r") as file:
            readable_data_2 = [line for line in file if line.strip()]
        for line in readable_data_2:
            assert __name__ not in line
        
        # Ensure logs from both loggers are in the json file
        with open(log_controller.json_file_path, "r") as file:
            json_data = [json.loads(line) for line in file if line.strip()]
        for line in json_data:
            if line["logger"] == "test_logger_2":
                assert line["message"] in [
                    "Debug message",
                    "Thread 2 performance information",
                    "Info message",
                    "Warning message",
                    "Error message",
                    "Critical!!!"
                ]
            else:
                assert line["message"] in [
                    "Something is happening behind the scenes...",
                    "This message contains some extra information",
                    "FUNCTION PERFORMANCE",
                    "Oopsy daisy! don't do that again :(",
                    "ERROR skjdbvwibuyfi8whf209[3r8h9weuvb]",
                    "SHUTTING DOWN BEEP BOOP",
                    "Failed tricky thingy!"
                ]
    

    def test_performance_level(self, test_json_logs):
        """Checks to make sure the performance level filters at the correct logging level"""
        logger, log_controller = test_json_logs
        performance_msg_2 = "Second performance log entry for testing"
        performance_msg_3 = "Third performance log entry for testing"

        logger.performance(performance_msg_2)
        logger.setLevel(logging.INFO)
        logger.performance(performance_msg_3)

        # Ensure logs from debug level show up, but after new level set they do not
        with open(log_controller.readable_file_path, "r") as file:
            readable_data = [line for line in file if line.strip()]
        for line in readable_data:
            if "PERFORMANCE" in line:
                assert performance_msg_3 not in line
                if performance_msg_2 in line:
                    assert True
                if "FUNCTION PERFORMANCE" in line:
                    assert True
    


