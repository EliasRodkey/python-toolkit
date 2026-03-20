"""
loggers.tests.test_logger_configs.py

Unit test for logger_configs.py using pytest
"""

import json
import logging
from logging.handlers import TimedRotatingFileHandler
import pytest
import os

from loggers.configure_logging import configure_logging
from loggers.handler_controller import HandlerController
from loggers.utils import LoggingMode, clear_logs


@pytest.fixture()
def test_handler():
    """Fixture to create fresh log file structure before each test"""
    
    try:
        # Setup: create log folders and files and configure logger, register log messages
        handler_controller = configure_logging()
        logger = logging.getLogger(__name__)

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

        yield handler_controller

    except Exception as e:
        print(e)
        raise

    finally:
        # Teardown: Ensure the session is closed and the files are deleted
        for name in handler_controller.handler_names():
            handler_controller.get_handler(name).flush()
            handler_controller.get_handler(name).close()
        logging.getLogger().handlers.clear()
        logger.handlers.clear()

        handler_controller._reset()
        clear_logs()


def test_configure_logging(test_handler):
    """Test class from LoggingHandlerController"""
    log_controller = test_handler
    root_logger = logging.getLogger()
    module_logger = logging.getLogger(__name__)
    rando_logger = logging.getLogger("poop")

    loggers = [root_logger, module_logger, rando_logger]

    module_message = "THIS IS A TEST OF THE MODULE LOGGER OUTPUT"
    rando_message = "THIS IS A TEST OF THE POOP LOGGER OUTPUT"
    module_logger.warning(module_message)
    rando_logger.error(rando_message)
     
    for name, handler in log_controller.handlers.items():
        assert handler in root_logger.handlers
    
    with open(log_controller.get_handler("main").baseFilename, "r") as f:
        lines = [line for line in f]
    
    module_captured = False
    rando_captured = False
    for line in lines:
        if line.endswith(f"{module_message}\n"):
            module_captured = True
        elif line.endswith(f"{rando_message}\n"):
            rando_captured = True
    
    assert module_captured and rando_captured


def test_json_log_file_creation(test_handler):
    """Makes sure the JSON log file is created and formatted correctly"""
    log_controller = test_handler

    with open(log_controller.json_file_path, "r") as file:
        data = [json.loads(line) for line in file if line.strip()]

    assert len(data) == 7
    
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


def test_add_new_run_name_logger(test_handler):
    """Adds a new logger and run name. Should create a new readable log file and log messages should also go to existing json file"""
    log_controller = test_handler

    # Create and configure a new logger with a different run name
    logger_2 = logging.getLogger("test_logger_2")
    log_controller.add_file_handler("thread_2")

    logger_2.debug("Debug message")
    logger_2.performance("Thread 2 performance information", extra={"step": "time delta"})
    logger_2.info("Info message")
    logger_2.warning("Warning message")
    logger_2.error("Error message")
    logger_2.critical("Critical!!!")

    # Check that the new readable log file was created and is accessible from the original log controller obj
    readable_file_path_2 = log_controller.get_handler("thread_2").baseFilename
    assert os.path.exists(readable_file_path_2)

    # Ensure logs from logger_2 are not in logger readable log file
    with open(log_controller.get_handler("main").baseFilename, "r") as file:
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


@pytest.fixture()
def test_mode_test(tmp_path):
    """Fixture for DAILY_DIRECTORY mode using an isolated temp directory."""
    handler_controller = configure_logging(log_directory=str(tmp_path), mode=LoggingMode.DAILY_DIRECTORY)
    yield handler_controller
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler_controller._reset()


@pytest.fixture()
def test_mode_production(tmp_path):
    """Fixture for BASIC_ROTATING_HANDLER mode using an isolated temp directory."""
    handler_controller = configure_logging(log_directory=str(tmp_path), mode=LoggingMode.BASIC_ROTATING_HANDLER)
    yield handler_controller
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler_controller._reset()


@pytest.fixture()
def test_mode_rotating_override(tmp_path):
    """Fixture to test rotating=True override on a non-rotating mode."""
    handler_controller = configure_logging(
        log_directory=str(tmp_path),
        mode=LoggingMode.DIRECTORY_PER_RUN,
        rotating=True,
    )
    yield handler_controller
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler_controller._reset()


def test_test_mode_no_stream_handler(test_mode_test):
    """DAILY_DIRECTORY mode should not create a stream handler on the controller."""
    assert test_mode_test.stream_handler is None
    assert "stream" not in test_mode_test.handlers


def test_test_mode_daily_folder(test_mode_test):
    """DAILY_DIRECTORY mode run_directory should be a daily folder (no per-run subfolder)."""
    lc = test_mode_test
    folder_name = os.path.basename(lc.run_directory)
    assert len(folder_name) == 10  # YYYY-MM-DD
    assert folder_name.count("-") == 2


def test_production_mode_stream_handler_at_warning(test_mode_production):
    """BASIC_ROTATING_HANDLER mode stream handler should be at WARNING level."""
    lc = test_mode_production
    assert lc.stream_handler is not None
    assert lc.stream_handler.level == logging.WARNING


def test_production_mode_timed_rotating_json_handler(test_mode_production):
    """BASIC_ROTATING_HANDLER mode should use TimedRotatingFileHandler for the JSON log."""
    lc = test_mode_production
    assert isinstance(lc.json_file_handler, TimedRotatingFileHandler)


def test_rotating_override_uses_timed_rotating_handler(test_mode_rotating_override):
    """rotating=True should use TimedRotatingFileHandler regardless of mode."""
    lc = test_mode_rotating_override
    assert isinstance(lc.json_file_handler, TimedRotatingFileHandler)
