"""
loggers.tests.test_json_log_parser.py

Unit test for json_log_parser.py using pytest
"""

import logging
import pytest

from loggers.json_log_parser import JSONLogParser, LogRecord
from loggers.handler_controller import HandlerController
from loggers.utils import clear_logs, add_performance_level


@pytest.fixture()
def test_json_log_parsing():
    """Fixture to create fresh log file structure before each test"""
    
    try:
        # Setup: create log folders and files and configure logger, register log messages
        add_performance_level()
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
        assert level_counts["DEBUG"] == 4
        assert level_counts["INFO"] == 2
        assert level_counts["WARNING"] == 2
        assert level_counts["ERROR"] == 2
        assert level_counts["CRITICAL"] == 1
        assert level_counts["PERFORMANCE"] == 3

        module_counts = log_parser.module_counts
        assert module_counts[__name__] == 14

        func_counts = log_parser.func_counts
        assert func_counts["test_json_log_parsing"] == 14
    

    def test_filter_by_level(self, test_json_log_parsing):
        """Tests filtering log records by level"""
        logger, log_controller, log_parser = test_json_log_parsing

        log_parser.load()

        debug_logs = log_parser.filter_by_level("DEBUG")
        assert len(debug_logs) == 4
        for record in debug_logs:
            assert record.level == "DEBUG"

        performance_info_warning_logs = log_parser.filter_by_level("PERFORMANCE", "INFO", "WARNING")
        assert len(performance_info_warning_logs) == 7
        for record in performance_info_warning_logs:
            assert record.level in ["PERFORMANCE", "INFO", "WARNING"]

        error_logs = log_parser.filter_by_level("ERROR")
        assert len(error_logs) == 2
        for record in error_logs:
            assert record.level == "ERROR"
        
        warning_and_critical_logs = log_parser.filter_by_level("WARNING", "CRITICAL")
        assert len(warning_and_critical_logs) == 3
        for record in warning_and_critical_logs:
            assert record.level in ["WARNING", "CRITICAL"]
    

    def test_filter_by_time(self, test_json_log_parsing):
        """Tests filtering log records by time"""
        logger, log_controller, log_parser = test_json_log_parsing

        log_parser.load()

        all_logs = log_parser.filter_by_time()
        assert len(all_logs) == 14

        first_half_logs = log_parser.filter_by_time(end_date=all_logs[6].timestamp)

        assert len(first_half_logs) == 7
        for record in first_half_logs:
            assert record.timestamp <= all_logs[6].timestamp

        second_half_logs = log_parser.filter_by_time(start_date=all_logs[7].timestamp)
        assert len(second_half_logs) == 7
        for record in second_half_logs:
            assert record.timestamp >= all_logs[7].timestamp

        middle_logs = log_parser.filter_by_time(start_date=all_logs[4].timestamp, end_date=all_logs[9].timestamp)
        assert len(middle_logs) == 6
        for record in middle_logs:
            assert all_logs[4].timestamp <= record.timestamp <= all_logs[9].timestamp
        
        no_logs = log_parser.filter_by_time(start_date=all_logs[-1].timestamp, end_date=all_logs[0].timestamp)
        assert len(no_logs) == 0
    

    def test_get_extra(self, test_json_log_parsing):
        """Tests getting extra fields from log records"""
        logger, log_controller, log_parser = test_json_log_parsing

        log_parser.load()

        records = log_parser.records

        debug1_extra = log_parser.get_extra(records[0], "debug_num")
        assert debug1_extra == 1

        warning_code_extra = log_parser.get_extra(records[2], "warning_code")
        assert warning_code_extra == 1234

        func_status_extra = log_parser.get_extra(records[10], "func_status")
        assert func_status_extra == "FAIL"

        missing_extra = log_parser.get_extra(records[1], "non_existent_key", default="DEFAULT_VALUE")
        assert missing_extra == "DEFAULT_VALUE"

    
    def test_filter_by_extra(self, test_json_log_parsing):
        """Tests filtering log records by extra fields"""
        logger, log_controller, log_parser = test_json_log_parsing

        log_parser.load()

        debug_logs = log_parser.filter_by_extra("debug_num")
        assert len(debug_logs) == 4
        assert debug_logs[1].message == "This is a second debug message"

        func_fail_logs = log_parser.filter_by_extra("func_status")
        assert len(func_fail_logs) == 1
        assert func_fail_logs[0].message == "Failed tricky thingy!"

        no_logs_with_extra = log_parser.filter_by_extra("non_existent_key")
        assert len(no_logs_with_extra) == 0
        assert type(no_logs_with_extra) == list
    

    def test_get_records_by_id(self, test_json_log_parsing):
        """Tests getting log records by their assigned ID"""
        logger, log_controller, log_parser = test_json_log_parsing

        log_parser.load()

        for i in range(14):
            record = log_parser.get_records_by_id(i)
            assert record.id == i
            assert type(record) == LogRecord
        
        records = log_parser.get_records_by_id([0, 12, 3, 14])
        assert records[0].message == "Something is happening behind the scenes..."
        assert records[1].message == "This is a second debug message"
        assert records[2].message == "FINALY FUNCTION PERFORMANCE"
        assert type(records) == list

        with pytest.raises(ValueError):
            log_parser.get_records_by_id("13")

    
    def test_to_dataframe(self, test_json_log_parsing):
        """Tests converting log records to pandas dataframe"""
        import pandas as pd

        logger, log_controller, log_parser = test_json_log_parsing

        log_parser.load()

        df_all = log_parser.to_dataframe()
        assert type(df_all) == pd.DataFrame
        assert len(df_all) == 14
        assert "level" in df_all.columns
        assert "message" in df_all.columns
        assert "timestamp" in df_all.columns
        assert "extra" not in df_all.columns
        assert "debug_num" in df_all.columns

        filtered_logs = log_parser.filter_by_level("ERROR", "CRITICAL")
        df_filtered = log_parser.to_dataframe(filtered_logs)
        assert type(df_filtered) == pd.DataFrame
        assert len(df_filtered) == 3
        for level in df_filtered["level"]:
            assert level in ["ERROR", "CRITICAL"]

    
    def test_top_messages(self, test_json_log_parsing):
        """Tests getting the top n messages from the log records"""
        logger, log_controller, log_parser = test_json_log_parsing

        log_parser.load()

        random_top_messages = log_parser.top_messages(5)  # Warm up call, see what happens
        assert type(random_top_messages) == list
        assert type(random_top_messages[0]) == tuple
        assert len(random_top_messages) == 5
        assert random_top_messages[0][1] == 1 # Since all messages unique at this point, top message should be 1 occurrence

        logger.debug("Repeated message for testing top messages")
        logger.info("Repeated message for testing top messages")
        logger.warning("Repeated message for testing top messages")
        logger.info("Another different repeated message")
        logger.info("Another different repeated message")

        log_parser.load()

        top_messages = log_parser.top_messages(3)
        import pprint
        pprint.pprint(top_messages)
        assert top_messages[0][0] == "Repeated message for testing top messages"
        assert top_messages[0][1] == 3
        assert top_messages[1][0] == "Another different repeated message"
        assert top_messages[1][1] == 2
        assert top_messages[2][0] == "Something is happening behind the scenes..."