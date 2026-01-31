"""
loggers.tests.test_logger_configs.py

Unit test for logger_configs.py using pytest
"""

import json
import logging
import pytest
import os

from loggers.handler_controller import HandlerController
from loggers.utils import clear_logs, add_performance_level


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
        # pass
        for name in handler_controller.handler_names:
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
