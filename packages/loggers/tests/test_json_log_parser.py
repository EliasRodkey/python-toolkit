"""
loggers.tests.test_json_log_parser.py

Unit test for json_log_parser.py using pytest
"""

import logging
import pytest

from loggers.json_log_parser import JSONLogParser, LogRecord
from loggers.logger_configs import configure_logger
from loggers.utils import clear_logs, add_performance_level

add_performance_level()


@pytest.fixture()
def test_json_log_parsing():
    """Fixture to create fresh log file structure before each test"""
    
    try:
        # Setup: create log folders and files and configure logger, register log messages
        logger = logging.getLogger(__name__)
        log_controller = configure_logger(logger)

        logger.debug("Something is happening behind the scenes...", extra={"debug_num": 1})
        logger.info("This message contains some extra information", extra={"var_1" : True, "var_2" : "ERROR"})
        logger.warning("Something might be going wrong...", extra={"warning_code": 1234})
        logger.debug("This is a second debug message", extra={"debug_num": 2})
        logger.performance("FUNCTION PERFORMANCE")
        logger.warning("Oopsy daisy! don't do that again :(")
        logger.info("Another piece of useful information about what is going on")
        logger.error("ERROR skjdbvwibuyfi8whf209[3r8h9weuvb]")
        logger.debug("Yet another debug message for testing", extra={"debug_num": 3})
        logger.performance("FAST PERFORMANCE, WANNA SEE ME DO IT AGAIN?")

        try:
            new_num = 6 / 0
        except Exception as e:
            logger.exception("Failed tricky thingy!", extra={"func_status": "FAIL"})
        
        logger.debug("I think maybe everything is okay now...", extra={"debug_num": 4})
        logger.performance("FINALY FUNCTION PERFORMANCE")
        logger.critical("SHUTTING DOWN BEEP BOOP")

        log_parser = JSONLogParser(log_controller.json_file_path)

        yield logger, log_controller, log_parser

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



class TestJSONLogParser:

    def test_load_json_logs(self, test_json_log_parsing):
        """Checks if the json logs load properly"""
        logger, log_controller, log_parser = test_json_log_parsing

        log_parser.load()

        assert len(log_parser.records) == 14, "Not all log record were gathered"
        assert type(log_parser.records[0]) == LogRecord
        assert log_parser.records[0].level == "DEBUG"
    

    def test_record_metrics(self, test_json_log_parsing):
        """Tests that the log record metrics are properly recorded"""
        logger, log_controller, log_parser = test_json_log_parsing

        log_parser.load()

        from pprint import pprint
        level_counts = log_parser.level_counts
        pprint(level_counts)
        assert level_counts["DEBUG"] == 4
        assert level_counts["INFO"] == 2
        assert level_counts["WARNING"] == 2
        assert level_counts["ERROR"] == 2
        assert level_counts["CRITICAL"] == 1
        assert level_counts["PERFORMANCE"] == 3

        module_counts = log_parser.module_counts
        pprint(module_counts)
        assert module_counts[__name__] == 14

        func_counts = log_parser.func_counts
        pprint(func_counts)
        assert func_counts["test_json_log_parsing"] == 14

