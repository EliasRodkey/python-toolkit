"""
tests.test_loggers

Tests for get_logger(), logger.perf() context manager, and logger.timed()
decorator.
"""
import json
import logging
import warnings
import os

import pytest
import structlog

from pleasant_loggers._config import configure_logging
from pleasant_loggers._handlers import HandlerController
from pleasant_loggers._levels import add_performance_level, PERFORMANCE_LEVEL_NUM
from pleasant_loggers._loggers import get_logger
from pleasant_loggers._modes import DIRECTORY_PER_RUN, BASIC_JSON_FILE


# ---------------------------------------------------------------------------
# Fixtures / teardown
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset():
    HandlerController._reset()
    structlog.reset_defaults()
    logging.getLogger().handlers.clear()
    yield
    HandlerController._reset()
    structlog.reset_defaults()
    logging.getLogger().handlers.clear()


@pytest.fixture()
def configured(tmp_path):
    add_performance_level()
    lc = configure_logging(log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN)
    return lc


def _read_json_records(lc) -> list[dict]:
    """Read and parse all NDJSON records from the controller's JSON log file."""
    with open(lc.json_file_path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


# ---------------------------------------------------------------------------
# get_logger() before configure_logging()
# ---------------------------------------------------------------------------

class TestGetLoggerBeforeConfigure:

    def test_warns_when_called_before_configure(self):
        """get_logger() must emit a UserWarning when called before configure_logging()."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            logger = get_logger(__name__)
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "configure_logging" in str(w[0].message).lower()

    def test_returns_logger_even_before_configure(self):
        """get_logger() must return a logger object even before configure_logging()."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            logger = get_logger(__name__)
            assert logger is not None


# ---------------------------------------------------------------------------
# get_logger() after configure_logging()
# ---------------------------------------------------------------------------

class TestGetLoggerAfterConfigure:

    def test_no_warning_after_configure(self, configured):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            get_logger(__name__)
            user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
            assert len(user_warnings) == 0

    def test_returns_logger_with_perf_method(self, configured):
        logger = get_logger(__name__)
        assert hasattr(logger, "perf")

    def test_returns_logger_with_timed_method(self, configured):
        logger = get_logger(__name__)
        assert hasattr(logger, "timed")

    def test_info_message_logged_to_json(self, configured):
        logger = get_logger(__name__)
        logger.info("hello from structlog", extra_field="test_value")
        records = _read_json_records(configured)
        events = [r["event"] for r in records]
        assert "hello from structlog" in events

    def test_flat_kwargs_appear_in_json_record(self, configured):
        logger = get_logger(__name__)
        logger.info("kwarg test", batch_id=42)
        records = _read_json_records(configured)
        matching = [r for r in records if r.get("event") == "kwarg test"]
        assert len(matching) == 1
        assert matching[0]["batch_id"] == 42


# ---------------------------------------------------------------------------
# logger.perf() — context manager
# ---------------------------------------------------------------------------

class TestPerf:

    def test_perf_emits_performance_record(self, configured):
        """perf() must emit a PERFORMANCE-level record after the block exits."""
        logger = get_logger(__name__)
        with logger.perf("my_operation", job_id=1):
            pass
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert len(perf_records) == 1

    def test_perf_record_has_duration_ms(self, configured):
        logger = get_logger(__name__)
        with logger.perf("timing_test"):
            pass
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert "duration_ms" in perf_records[0]
        assert isinstance(perf_records[0]["duration_ms"], float)

    def test_perf_record_status_ok_on_success(self, configured):
        logger = get_logger(__name__)
        with logger.perf("success_op"):
            pass
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert perf_records[0]["status"] == "ok"

    def test_perf_record_status_error_on_exception(self, configured):
        """On exception, status must be 'error' and error_type must be set."""
        logger = get_logger(__name__)
        with pytest.raises(ValueError):
            with logger.perf("failing_op"):
                raise ValueError("boom")
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert len(perf_records) == 1
        assert perf_records[0]["status"] == "error"

    def test_perf_record_error_type_on_exception(self, configured):
        logger = get_logger(__name__)
        with pytest.raises(RuntimeError):
            with logger.perf("failing_op"):
                raise RuntimeError("oops")
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert perf_records[0]["error_type"] == "RuntimeError"

    def test_perf_re_raises_exception(self, configured):
        """perf() must not swallow exceptions."""
        logger = get_logger(__name__)
        with pytest.raises(ZeroDivisionError):
            with logger.perf("math_op"):
                _ = 1 / 0

    def test_perf_captures_kwargs_in_record(self, configured):
        logger = get_logger(__name__)
        with logger.perf("job_run", job_id=99):
            pass
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert perf_records[0].get("job_id") == 99

    def test_perf_event_name_in_record(self, configured):
        logger = get_logger(__name__)
        with logger.perf("my_named_op"):
            pass
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert perf_records[0]["event"] == "my_named_op"

    def test_perf_duration_ms_is_non_negative(self, configured):
        logger = get_logger(__name__)
        with logger.perf("quick_op"):
            pass
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert perf_records[0]["duration_ms"] >= 0.0


# ---------------------------------------------------------------------------
# logger.timed() — decorator
# ---------------------------------------------------------------------------

class TestTimed:

    def test_timed_emits_performance_record(self, configured):
        """timed() must emit a PERFORMANCE-level record after the function returns."""
        logger = get_logger(__name__)

        @logger.timed("decorated_fn")
        def my_fn():
            return 42

        my_fn()
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert len(perf_records) == 1

    def test_timed_record_has_duration_ms(self, configured):
        logger = get_logger(__name__)

        @logger.timed("decorated_fn")
        def my_fn():
            pass

        my_fn()
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert "duration_ms" in perf_records[0]

    def test_timed_returns_function_result(self, configured):
        """timed() must not swallow the return value."""
        logger = get_logger(__name__)

        @logger.timed("fn_with_return")
        def my_fn():
            return 123

        result = my_fn()
        assert result == 123

    def test_timed_captures_function_args(self, configured):
        """timed() should capture the function's call-time arguments."""
        logger = get_logger(__name__)

        @logger.timed("fn_with_args")
        def process(batch_id, user):
            pass

        process(batch_id=7, user="elias")
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert perf_records[0].get("batch_id") == 7
        assert perf_records[0].get("user") == "elias"

    def test_timed_excludes_self_from_args(self, configured):
        """timed() must not include 'self' in the captured args."""
        logger = get_logger(__name__)

        class Worker:
            @logger.timed("worker_method")
            def run(self, task_id):
                pass

        Worker().run(task_id=5)
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert "self" not in perf_records[0]
        assert perf_records[0].get("task_id") == 5

    def test_timed_status_ok_on_success(self, configured):
        logger = get_logger(__name__)

        @logger.timed("ok_fn")
        def my_fn():
            pass

        my_fn()
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert perf_records[0]["status"] == "ok"

    def test_timed_status_error_on_exception(self, configured):
        logger = get_logger(__name__)

        @logger.timed("error_fn")
        def my_fn():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            my_fn()
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert perf_records[0]["status"] == "error"
        assert perf_records[0]["error_type"] == "ValueError"

    def test_timed_re_raises_exception(self, configured):
        """timed() must not swallow exceptions."""
        logger = get_logger(__name__)

        @logger.timed("failing_fn")
        def my_fn():
            raise RuntimeError("fail")

        with pytest.raises(RuntimeError):
            my_fn()

    def test_timed_event_name_in_record(self, configured):
        logger = get_logger(__name__)

        @logger.timed("my_event_name")
        def my_fn():
            pass

        my_fn()
        records = _read_json_records(configured)
        perf_records = [r for r in records if r.get("level", "").upper() == "PERFORMANCE"]
        assert perf_records[0]["event"] == "my_event_name"
