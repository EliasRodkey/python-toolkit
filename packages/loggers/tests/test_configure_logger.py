"""
Tests for configure_logger behavior: JSON logging, per-run readable logs, and performance level filtering.
"""

import json
import logging
import pytest
import os

from loggers.configure_logger import configure_logger
from loggers.utils import clear_logs, add_performance_level


@pytest.fixture()
def configured_logs():
	"""Create fresh log file structure and populate with a set of messages"""
	add_performance_level()
	logger = logging.getLogger(__name__)
	log_controller = configure_logger(logger)

	logger.debug("Something is happening behind the scenes...")
	logger.info("This message contains some extra information", extra={"var_1": True, "var_2": "ERROR"})
	logger.performance("FUNCTION PERFORMANCE")
	logger.warning("Oopsy daisy! don't do that again :(")
	logger.error("ERROR skjdbvwibuyfi8whf209[3r8h9weuvb]")
	logger.critical("SHUTTING DOWN BEEP BOOP")
	try:
		6 / 0
	except Exception:
		logger.exception("Failed tricky thingy!", extra={"func_status": "FAIL"})

	yield logger, log_controller

	# Teardown: ensure handlers closed and files removed
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


class TestConfigureLogger:
	"""Tests that verify configure_logger produced the expected files and behavior"""

	def test_json_log_file_creation(self, configured_logs):
		"""JSON log file should exist and contain expected structured entries"""
		logger, log_controller = configured_logs
		assert os.path.exists(log_controller.json_file_path)

		with open(log_controller.json_file_path, "r") as file:
			data = [json.loads(line) for line in file if line.strip()]

		assert len(data) == 7, "Missing log entries"

		for entry in data:
			for key in ("timestamp", "level", "logger", "message", "module", "function", "line", "exception", "extra"):
				assert key in entry, f"missing '{key}' in log entry"

	def test_add_new_run_name_logger(self, configured_logs):
		"""Creating a new logger with a different run name should create its own readable file while still logging to shared JSON"""
		logger, log_controller = configured_logs

		logger_2 = logging.getLogger("test_logger_2")
		log_controller_2 = configure_logger(logger_2, run_name="thread_2")

		readable_file_path_2 = log_controller_2.readable_file_path
		assert os.path.exists(readable_file_path_2)
		assert readable_file_path_2 == log_controller._run_names["thread_2"]["path"]

		# Ensure logger_2 logs don't appear in original readable log
		with open(log_controller.readable_file_path, "r") as file:
			readable_data = [line for line in file if line.strip()]
		for line in readable_data:
			assert "thread_2" not in line

		# Ensure original logs don't appear in logger_2 readable log
		with open(readable_file_path_2, "r") as file:
			readable_data_2 = [line for line in file if line.strip()]
		for line in readable_data_2:
			assert __name__ not in line

		# Ensure both sets of logs are present in the shared json file
		with open(log_controller.json_file_path, "r") as file:
			json_data = [json.loads(line) for line in file if line.strip()]
		messages_for_2 = {
			"Debug message",
			"Thread 2 performance information",
			"Info message",
			"Warning message",
			"Error message",
			"Critical!!!",
		}
		messages_for_original = {
			"Something is happening behind the scenes...",
			"This message contains some extra information",
			"FUNCTION PERFORMANCE",
			"Oopsy daisy! don't do that again :(",
			"ERROR skjdbvwibuyfi8whf209[3r8h9weuvb]",
			"SHUTTING DOWN BEEP BOOP",
			"Failed tricky thingy!",
		}
		for entry in json_data:
			if entry["logger"] == "test_logger_2":
				assert entry["message"] in messages_for_2
			else:
				assert entry["message"] in messages_for_original

		# Cleanup handlers created during test
		log_controller_2.handlers["json"].flush()
		log_controller_2.handlers["json"].close()
		logger_2.removeHandler(log_controller_2.handlers["json"])

		log_controller_2.handlers["stream"].flush()
		log_controller_2.handlers["stream"].close()
		logger_2.removeHandler(log_controller_2.handlers["stream"])

		for name, handler in log_controller_2.handlers["readable"].items():
			handler.flush()
			handler.close()
			logger_2.removeHandler(handler)

	def test_performance_level(self, configured_logs):
		"""Performance logs should obey the configured performance level filtering"""
		logger, log_controller = configured_logs
		performance_msg_2 = "Second performance log entry for testing"
		performance_msg_3 = "Third performance log entry for testing"

		logger.performance(performance_msg_2)
		logger.setLevel(logging.INFO)
		logger.performance(performance_msg_3)

		# Ensure debug-level performance entries after raising level are filtered from readable file
		with open(log_controller.readable_file_path, "r") as file:
			readable_data = [line for line in file if line.strip()]

		assert any(performance_msg_2 in line for line in readable_data)
		assert all(performance_msg_3 not in line for line in readable_data)
