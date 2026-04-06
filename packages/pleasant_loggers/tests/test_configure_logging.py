"""
tests.test_configure_logging

Integration tests for configure_logging(): all 5 built-in modes, fine-grained
overrides, second-call RuntimeError, structlog processor chain wiring, and
actual file creation/content.
"""
import dataclasses
import json
import logging
import os

import pytest
import structlog

from pleasant_loggers._config import configure_logging
from pleasant_loggers._handlers import HandlerController
from pleasant_loggers._modes import (
    BASIC_SINGLE_FILE,
    BASIC_JSON_FILE,
    DIRECTORY_PER_RUN,
    DAILY_DIRECTORY,
    BASIC_ROTATING_HANDLER,
    LoggingMode,
    DirectoryLayout,
)
from pleasant_loggers._utils import clear_logs


# ---------------------------------------------------------------------------
# Fixtures / teardown
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_between_tests():
    """Reset HandlerController and structlog before and after every test."""
    HandlerController._reset()
    structlog.reset_defaults()
    logging.getLogger().handlers.clear()
    yield
    HandlerController._reset()
    structlog.reset_defaults()
    logging.getLogger().handlers.clear()


@pytest.fixture()
def lc_per_run(tmp_path):
    lc = configure_logging(log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN)
    logger = logging.getLogger(__name__)
    logger.info("test info message", extra={"tag": "fixture"})
    logger.debug("test debug message")
    logger.warning("test warning message")
    return lc


@pytest.fixture()
def lc_daily(tmp_path):
    return configure_logging(log_directory=str(tmp_path), mode=DAILY_DIRECTORY)


@pytest.fixture()
def lc_basic_single(tmp_path):
    return configure_logging(log_directory=str(tmp_path), mode=BASIC_SINGLE_FILE)


@pytest.fixture()
def lc_basic_json(tmp_path):
    return configure_logging(log_directory=str(tmp_path), mode=BASIC_JSON_FILE)


@pytest.fixture()
def lc_rotating(tmp_path):
    return configure_logging(log_directory=str(tmp_path), mode=BASIC_ROTATING_HANDLER)


# ---------------------------------------------------------------------------
# Returns HandlerController
# ---------------------------------------------------------------------------

class TestReturnValue:

    def test_returns_handler_controller(self, tmp_path):
        lc = configure_logging(log_directory=str(tmp_path), mode=BASIC_SINGLE_FILE)
        assert isinstance(lc, HandlerController)


# ---------------------------------------------------------------------------
# Second call raises RuntimeError
# ---------------------------------------------------------------------------

class TestSecondCallRaises:

    def test_second_call_raises_runtime_error(self, tmp_path):
        configure_logging(log_directory=str(tmp_path), mode=BASIC_SINGLE_FILE)
        with pytest.raises(RuntimeError, match="configure_logging"):
            configure_logging(log_directory=str(tmp_path), mode=BASIC_SINGLE_FILE)


# ---------------------------------------------------------------------------
# validate() is called
# ---------------------------------------------------------------------------

class TestValidation:

    def test_invalid_mode_raises_value_error(self, tmp_path):
        bad_mode = LoggingMode(
            stream=False, stream_level=logging.INFO,
            file=False, file_level=logging.DEBUG,
            json=False, json_level=logging.DEBUG,
            directory_layout=DirectoryLayout.FLAT,
        )
        with pytest.raises(ValueError):
            configure_logging(log_directory=str(tmp_path), mode=bad_mode)


# ---------------------------------------------------------------------------
# Root logger is configured
# ---------------------------------------------------------------------------

class TestRootLoggerHandlers:

    def test_root_logger_has_handlers_after_configure(self, lc_per_run):
        root = logging.getLogger()
        assert len(root.handlers) > 0

    def test_root_logger_level_is_debug(self, lc_per_run):
        assert logging.getLogger().level == logging.DEBUG


# ---------------------------------------------------------------------------
# JSON log output — flat NDJSON with correct fields
# ---------------------------------------------------------------------------

class TestJsonOutput:

    def test_json_file_created(self, lc_per_run):
        assert os.path.exists(lc_per_run.json_file_path)

    def test_json_records_are_flat_ndjson(self, lc_per_run):
        """Every line in the JSON log must be a valid flat JSON object."""
        with open(lc_per_run.json_file_path, encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        assert len(lines) > 0
        for line in lines:
            record = json.loads(line)
            assert isinstance(record, dict)

    def test_json_records_have_required_fields(self, lc_per_run):
        with open(lc_per_run.json_file_path, encoding="utf-8") as f:
            records = [json.loads(l) for l in f if l.strip()]
        required = {"timestamp", "level", "event", "logger", "func_name", "module", "lineno"}
        for record in records:
            for field in required:
                assert field in record, f"Missing field {field!r} in record: {record}"

    def test_json_records_no_nested_extra(self, lc_per_run):
        """v2 output must be flat — no 'extra' key, no 'message' key."""
        with open(lc_per_run.json_file_path, encoding="utf-8") as f:
            records = [json.loads(l) for l in f if l.strip()]
        for record in records:
            assert "extra" not in record
            assert "message" not in record

    def test_extra_dict_flattened_into_record(self, lc_per_run):
        """extra={'tag': 'fixture'} should appear as top-level 'tag' field."""
        with open(lc_per_run.json_file_path, encoding="utf-8") as f:
            records = [json.loads(l) for l in f if l.strip()]
        tagged = [r for r in records if r.get("tag") == "fixture"]
        assert len(tagged) >= 1

    def test_timestamp_is_iso_format(self, lc_per_run):
        with open(lc_per_run.json_file_path, encoding="utf-8") as f:
            records = [json.loads(l) for l in f if l.strip()]
        from datetime import datetime
        for record in records:
            ts = record["timestamp"]
            # Should parse without error
            datetime.fromisoformat(ts.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Fine-grained overrides (dataclasses.replace)
# ---------------------------------------------------------------------------

class TestOverrides:

    def test_stream_false_suppresses_stream_handler(self, tmp_path):
        lc = configure_logging(log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN, stream=False)
        assert lc.stream_handler is None

    def test_stream_true_on_daily_directory(self, tmp_path):
        lc = configure_logging(log_directory=str(tmp_path), mode=DAILY_DIRECTORY, stream=True)
        assert lc.stream_handler is not None

    def test_json_false_suppresses_json_handler(self, tmp_path):
        lc = configure_logging(log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN, json=False)
        assert lc.json_file_handler is None

    def test_file_false_suppresses_readable_handler(self, tmp_path):
        lc = configure_logging(log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN, file=False)
        assert lc.readable_file_handler is None

    def test_stream_level_override(self, tmp_path):
        lc = configure_logging(
            log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN,
            stream_level=logging.WARNING
        )
        assert lc.stream_handler.level == logging.WARNING

    def test_file_level_override(self, tmp_path):
        lc = configure_logging(
            log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN,
            file_level=logging.WARNING
        )
        assert lc.readable_file_handler.level == logging.WARNING

    def test_json_level_override(self, tmp_path):
        lc = configure_logging(
            log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN,
            json_level=logging.WARNING
        )
        assert lc.json_file_handler.level == logging.WARNING

    def test_built_in_mode_instances_not_mutated(self, tmp_path):
        """dataclasses.replace() must not mutate the built-in mode instance."""
        original_stream = DIRECTORY_PER_RUN.stream
        configure_logging(log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN, stream=False)
        assert DIRECTORY_PER_RUN.stream == original_stream


# ---------------------------------------------------------------------------
# BASIC_SINGLE_FILE mode
# ---------------------------------------------------------------------------

class TestBasicSingleFile:

    def test_flat_directory(self, lc_basic_single, tmp_path):
        assert os.path.normpath(lc_basic_single.run_directory) == os.path.normpath(str(tmp_path))

    def test_no_json_handler(self, lc_basic_single):
        assert lc_basic_single.json_file_handler is None

    def test_has_stream_and_readable(self, lc_basic_single):
        assert lc_basic_single.stream_handler is not None
        assert lc_basic_single.readable_file_handler is not None

    def test_stream_level_is_info(self, lc_basic_single):
        assert lc_basic_single.stream_handler.level == logging.INFO


# ---------------------------------------------------------------------------
# BASIC_JSON_FILE mode
# ---------------------------------------------------------------------------

class TestBasicJsonFile:

    def test_flat_directory(self, lc_basic_json, tmp_path):
        assert os.path.normpath(lc_basic_json.run_directory) == os.path.normpath(str(tmp_path))

    def test_no_readable_handler(self, lc_basic_json):
        assert lc_basic_json.readable_file_handler is None

    def test_has_json_and_stream(self, lc_basic_json):
        assert lc_basic_json.json_file_handler is not None
        assert lc_basic_json.stream_handler is not None

    def test_json_file_exists(self, lc_basic_json):
        assert os.path.exists(lc_basic_json.json_file_path)


# ---------------------------------------------------------------------------
# DAILY_DIRECTORY mode
# ---------------------------------------------------------------------------

class TestDailyDirectory:

    def test_no_stream_handler(self, lc_daily):
        assert lc_daily.stream_handler is None

    def test_daily_folder_structure(self, lc_daily, tmp_path):
        folder_name = os.path.basename(lc_daily.run_directory)
        assert len(folder_name) == 10
        assert folder_name.count("-") == 2


# ---------------------------------------------------------------------------
# DIRECTORY_PER_RUN mode
# ---------------------------------------------------------------------------

class TestDirectoryPerRun:

    def test_nested_run_directory(self, lc_per_run, tmp_path):
        parts = os.path.relpath(lc_per_run.run_directory, str(tmp_path)).split(os.sep)
        assert len(parts) == 2

    def test_has_all_handlers(self, lc_per_run):
        assert lc_per_run.json_file_handler is not None
        assert lc_per_run.readable_file_handler is not None
        assert lc_per_run.stream_handler is not None


# ---------------------------------------------------------------------------
# BASIC_ROTATING_HANDLER mode
# ---------------------------------------------------------------------------

class TestBasicRotatingHandler:
    from logging.handlers import TimedRotatingFileHandler

    def test_timed_rotating_json_handler(self, lc_rotating):
        from logging.handlers import TimedRotatingFileHandler
        assert isinstance(lc_rotating.json_file_handler, TimedRotatingFileHandler)

    def test_stream_level_is_warning(self, lc_rotating):
        assert lc_rotating.stream_handler.level == logging.WARNING

    def test_flat_directory(self, lc_rotating, tmp_path):
        assert os.path.normpath(lc_rotating.run_directory) == os.path.normpath(str(tmp_path))

