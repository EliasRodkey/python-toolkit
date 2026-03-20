"""
loggers.tests.test_logger_configs.py

Unit test for logger_configs.py using pytest
"""

import json
import logging
from logging.handlers import TimedRotatingFileHandler
import pytest
import os

from loggers.handler_controller import HandlerController
from loggers.utils import LoggingMode, clear_logs, add_performance_level


@pytest.fixture()
def test_handler():
    """Fixture to create fresh log file structure before each test"""
    
    try:
        # Setup: create log folders and files and configure logger, register log messages
        add_performance_level()
        logger = logging.getLogger(__name__)
        handler_controller = HandlerController()
        logger.addHandler(handler_controller.json_file_handler)
        logger.addHandler(handler_controller.get_handler("main"))
        if handler_controller.stream_handler is not None:
            logger.addHandler(handler_controller.stream_handler)

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
            logger.removeHandler(handler_controller.handlers[name])

        handler_controller._reset()
        clear_logs()


class TestHandlerControler:
    """Test class from LoggingHandlerController"""

    def test_json_log_file_creation(self, test_handler):
        """Makes sure the JSON log file is created and formatted correctly"""
        log_controller = test_handler
        assert os.path.exists(log_controller.json_file_path)
    

    def test_readable_log_file_creation(self, test_handler):
        """Makes sure the readable log file is created"""
        log_controller = test_handler
        assert os.path.exists(log_controller.get_handler("main").baseFilename)

    
    def test_get_handler(self, test_handler):
        """Tests the get_handler method of HandlerController"""
        log_controller = test_handler
        json_handler = log_controller.get_handler("json")
        assert json_handler == log_controller.json_file_handler
    

    def test_get_file_handler_doesnt_exist(slef, test_handler):
        """Tries to get a file handler that doesn't exist in the controller."""
        log_controller = test_handler

        try:
            log_controller.get_handler("NONE")

        except Exception as e:
            assert isinstance(e, KeyError)

    
    def test_add_file_handler(self, test_handler):
        """Adds a handler. Should create a new readable log file and log messages should also go to existing json file"""
        log_controller = test_handler

        # Create and configure a new logger with a different run name
        logger_2 = logging.getLogger("test_logger_2")
        log_controller.add_file_handler("file_2")
        logger_2.addHandler(log_controller.get_handler("file_2"))

        logger_2.debug("Debug message")

        # Check that the new readable log file was created and is accessible from the original log controller obj
        readable_file_path_2 = log_controller.get_handler("file_2").baseFilename
        assert os.path.exists(readable_file_path_2)
    

    def test_add_file_handler_exists(slef, test_handler):
        """Adds a new file handler that already exists in the controller."""
        log_controller = test_handler

        try:
            log_controller.add_file_handler("main")

        except Exception as e:
            assert isinstance(e, KeyError)
    

    def test_remove_handler(self, test_handler):
        """Tests the remove_handler function in HandlerController"""
        log_controller = test_handler

        log_controller.remove_handler("main")
        assert "main" not in log_controller.handler_names()
        assert "main" not in log_controller.handlers.keys()

        try:
            log_controller.get_handler("main")
        
        except Exception as e:
            assert isinstance(e, KeyError)
        
        log_controller.add_file_handler("main")
    

    def test_remove_file_handler_doesnt_exist(self, test_handler):
        """Tries to remove a file handler that doesn't exist in the controller."""
        log_controller = test_handler

        try:
            log_controller.remove_handler("NONE")

        except Exception as e:
            assert isinstance(e, KeyError)


    def test_reset_handler_controller(self, test_handler):
        """Tests the _reset method"""
        log_controller = test_handler

        log_controller._reset()

        assert log_controller._initialized == False
        assert log_controller.handlers == {}
        assert log_controller.json_file_handler == None

    def test_reset_completeness(self, test_handler):
        """_reset() should clear all class-level state, not just _initialized/handlers/json_file_handler."""
        log_controller = test_handler

        log_controller._reset()

        assert log_controller._initialized == False
        assert log_controller.handlers == {}
        assert log_controller.stream_handler is None
        assert log_controller.json_file_handler is None
        assert log_controller.run_directory == ""
        assert log_controller.log_datetime_stamp == ""
        assert log_controller.json_file_path == ""


@pytest.fixture()
def test_handler_test_mode(tmp_path):
    """Fixture for DAILY_DIRECTORY mode using an isolated temp directory."""
    add_performance_level()
    controller = HandlerController(log_directory=str(tmp_path), mode=LoggingMode.DAILY_DIRECTORY, stream=False)
    yield controller
    controller._reset()


@pytest.fixture()
def test_handler_production_mode(tmp_path):
    """Fixture for BASIC_ROTATING_HANDLER mode using an isolated temp directory."""
    add_performance_level()
    controller = HandlerController(
        log_directory=str(tmp_path),
        mode=LoggingMode.BASIC_ROTATING_HANDLER,
        stream_level=logging.WARNING,
        rotating=True,
    )
    yield controller
    controller._reset()


@pytest.fixture()
def test_handler_rotating_override(tmp_path):
    """Fixture to test rotating=True override on a non-rotating mode."""
    add_performance_level()
    controller = HandlerController(
        log_directory=str(tmp_path),
        mode=LoggingMode.DAILY_DIRECTORY,
        stream=False,
        rotating=True,
    )
    yield controller
    controller._reset()


class TestHandlerControllerModes:

    def test_test_mode_daily_folder(self, test_handler_test_mode):
        """TEST mode should use a daily folder only (no per-run subfolder)."""
        lc = test_handler_test_mode
        # run_directory should end with YYYY-MM-DD, not YYYY-MM-DD_HHMMSS
        folder_name = os.path.basename(lc.run_directory)
        assert len(folder_name) == 10  # YYYY-MM-DD
        assert folder_name.count("-") == 2

    def test_test_mode_no_stream_handler(self, test_handler_test_mode):
        """TEST mode should not create a stream handler."""
        lc = test_handler_test_mode
        assert lc.stream_handler is None
        assert "stream" not in lc.handlers

    def test_test_mode_files_created(self, test_handler_test_mode):
        """TEST mode should still create readable and JSON log files."""
        lc = test_handler_test_mode
        assert os.path.exists(lc.json_file_path)
        assert os.path.exists(lc.get_handler("main").baseFilename)

    def test_production_mode_uses_timed_rotating_handler(self, test_handler_production_mode):
        """PRODUCTION mode should use TimedRotatingFileHandler for the JSON log."""
        lc = test_handler_production_mode
        assert isinstance(lc.json_file_handler, TimedRotatingFileHandler)

    def test_production_mode_stream_level_is_warning(self, test_handler_production_mode):
        """PRODUCTION mode stream handler should be at WARNING level."""
        lc = test_handler_production_mode
        assert lc.stream_handler is not None
        assert lc.stream_handler.level == logging.WARNING

    def test_production_mode_flat_directory(self, test_handler_production_mode, tmp_path):
        """PRODUCTION mode should use the flat log_directory with no date subfolder."""
        lc = test_handler_production_mode
        assert os.path.normpath(lc.run_directory) == os.path.normpath(str(tmp_path))

    def test_mode_stored_as_class_variable(self, test_handler_test_mode):
        """The active mode should be stored on the class."""
        assert HandlerController.mode == LoggingMode.DAILY_DIRECTORY

    def test_rotating_override_uses_timed_rotating_handler(self, test_handler_rotating_override):
        """rotating=True should use TimedRotatingFileHandler regardless of mode."""
        lc = test_handler_rotating_override
        assert isinstance(lc.json_file_handler, TimedRotatingFileHandler)

    def test_json_false_override(self, tmp_path):
        """json=False on DIRECTORY_PER_RUN should suppress JSON handler."""
        add_performance_level()
        lc = HandlerController(
            log_directory=str(tmp_path),
            mode=LoggingMode.DIRECTORY_PER_RUN,
            json=False,
        )
        try:
            assert lc.json_file_handler is None
            assert "json" not in lc.handler_names()
        finally:
            lc._reset()

    def test_stream_false_override(self, tmp_path):
        """stream=False on DIRECTORY_PER_RUN should suppress the stream handler."""
        add_performance_level()
        lc = HandlerController(
            log_directory=str(tmp_path),
            mode=LoggingMode.DIRECTORY_PER_RUN,
            stream=False,
        )
        try:
            assert lc.stream_handler is None
            assert "stream" not in lc.handler_names()
        finally:
            lc._reset()


@pytest.fixture()
def test_handler_basic_single_file(tmp_path):
    """Fixture for BASIC_SINGLE_FILE mode using an isolated temp directory."""
    add_performance_level()
    controller = HandlerController(
        log_directory=str(tmp_path),
        mode=LoggingMode.BASIC_SINGLE_FILE,
        stream=True,
        stream_level=logging.INFO,
        file=True,
        json=False,
    )
    yield controller
    controller._reset()


@pytest.fixture()
def test_handler_basic_json_file(tmp_path):
    """Fixture for BASIC_JSON_FILE mode using an isolated temp directory."""
    add_performance_level()
    controller = HandlerController(
        log_directory=str(tmp_path),
        mode=LoggingMode.BASIC_JSON_FILE,
        stream=True,
        stream_level=logging.INFO,
        file=False,
        json=True,
    )
    yield controller
    controller._reset()


class TestHandlerControllerBasicModes:

    def test_basic_single_file_flat_directory(self, test_handler_basic_single_file, tmp_path):
        """BASIC_SINGLE_FILE run_directory should be the flat log_directory."""
        lc = test_handler_basic_single_file
        assert os.path.normpath(lc.run_directory) == os.path.normpath(str(tmp_path))

    def test_basic_single_file_no_json_handler(self, test_handler_basic_single_file):
        """BASIC_SINGLE_FILE should not create a JSON handler."""
        lc = test_handler_basic_single_file
        assert lc.json_file_handler is None
        assert "json" not in lc.handler_names()

    def test_basic_single_file_has_main_and_stream(self, test_handler_basic_single_file):
        """BASIC_SINGLE_FILE should have 'main' and 'stream' handlers."""
        lc = test_handler_basic_single_file
        assert "main" in lc.handler_names()
        assert "stream" in lc.handler_names()

    def test_basic_single_file_stream_at_info(self, test_handler_basic_single_file):
        """BASIC_SINGLE_FILE stream handler should be at INFO level."""
        lc = test_handler_basic_single_file
        assert lc.stream_handler is not None
        assert lc.stream_handler.level == logging.INFO

    def test_basic_json_file_flat_directory(self, test_handler_basic_json_file, tmp_path):
        """BASIC_JSON_FILE run_directory should be the flat log_directory."""
        lc = test_handler_basic_json_file
        assert os.path.normpath(lc.run_directory) == os.path.normpath(str(tmp_path))

    def test_basic_json_file_no_main_handler(self, test_handler_basic_json_file):
        """BASIC_JSON_FILE should not create a 'main' text file handler (file=False)."""
        lc = test_handler_basic_json_file
        assert "main" not in lc.handler_names()

    def test_basic_json_file_has_json_and_stream(self, test_handler_basic_json_file):
        """BASIC_JSON_FILE should have 'json' and 'stream' handlers."""
        lc = test_handler_basic_json_file
        assert "json" in lc.handler_names()
        assert "stream" in lc.handler_names()

    def test_basic_json_file_json_file_exists(self, test_handler_basic_json_file):
        """BASIC_JSON_FILE should create the JSON log file on disk."""
        lc = test_handler_basic_json_file
        assert os.path.exists(lc.json_file_path)
