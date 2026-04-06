"""
tests.test_handler_controller

Tests for HandlerController: path resolution per DirectoryLayout, handler
creation, json_file_path/log_directory exposure, singleton behaviour, and
_reset() completeness.
"""
import logging
from logging.handlers import TimedRotatingFileHandler
import os

import pytest

from pleasant_loggers._handlers import HandlerController
from pleasant_loggers._modes import (
    BASIC_SINGLE_FILE,
    BASIC_JSON_FILE,
    DIRECTORY_PER_RUN,
    DAILY_DIRECTORY,
    BASIC_ROTATING_HANDLER,
    DirectoryLayout,
    LoggingMode,
)
from pleasant_loggers._utils import clear_logs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_controller():
    """Ensure HandlerController is fully reset before and after every test."""
    HandlerController._reset()
    yield
    HandlerController._reset()


@pytest.fixture()
def controller_per_run(tmp_path):
    return HandlerController(log_directory=str(tmp_path), mode=DIRECTORY_PER_RUN)


@pytest.fixture()
def controller_daily(tmp_path):
    return HandlerController(log_directory=str(tmp_path), mode=DAILY_DIRECTORY)


@pytest.fixture()
def controller_flat(tmp_path):
    return HandlerController(log_directory=str(tmp_path), mode=BASIC_SINGLE_FILE)


@pytest.fixture()
def controller_json_file(tmp_path):
    return HandlerController(log_directory=str(tmp_path), mode=BASIC_JSON_FILE)


@pytest.fixture()
def controller_rotating(tmp_path):
    return HandlerController(log_directory=str(tmp_path), mode=BASIC_ROTATING_HANDLER)


# ---------------------------------------------------------------------------
# Singleton behaviour
# ---------------------------------------------------------------------------

class TestSingleton:

    def test_second_instantiation_raises(self, tmp_path):
        """HandlerController raises RuntimeError if instantiated twice."""
        HandlerController(log_directory=str(tmp_path), mode=BASIC_SINGLE_FILE)
        with pytest.raises(RuntimeError, match="HandlerController"):
            HandlerController(log_directory=str(tmp_path), mode=BASIC_SINGLE_FILE)

    def test_reset_allows_reinitialisation(self, tmp_path):
        """After _reset(), HandlerController can be instantiated again."""
        HandlerController(log_directory=str(tmp_path), mode=BASIC_SINGLE_FILE)
        HandlerController._reset()
        # Should not raise
        hc = HandlerController(log_directory=str(tmp_path), mode=BASIC_SINGLE_FILE)
        assert hc._initialized is True


# ---------------------------------------------------------------------------
# _reset() completeness
# ---------------------------------------------------------------------------

class TestReset:

    def test_reset_clears_initialized(self, controller_per_run):
        HandlerController._reset()
        assert HandlerController._initialized is False

    def test_reset_clears_handlers(self, controller_per_run):
        HandlerController._reset()
        assert HandlerController.handlers == {}

    def test_reset_clears_json_file_handler(self, controller_per_run):
        HandlerController._reset()
        assert HandlerController.json_file_handler is None

    def test_reset_clears_stream_handler(self, controller_per_run):
        HandlerController._reset()
        assert HandlerController.stream_handler is None

    def test_reset_clears_run_directory(self, controller_per_run):
        HandlerController._reset()
        assert HandlerController.run_directory == ""

    def test_reset_clears_log_datetime_stamp(self, controller_per_run):
        HandlerController._reset()
        assert HandlerController.log_datetime_stamp == ""

    def test_reset_clears_json_file_path(self, controller_per_run):
        HandlerController._reset()
        assert HandlerController.json_file_path == ""


# ---------------------------------------------------------------------------
# DIRECTORY_PER_RUN
# ---------------------------------------------------------------------------

class TestDirectoryPerRun:

    def test_run_directory_is_nested(self, controller_per_run, tmp_path):
        """PER_RUN: run_directory should be tmp/YYYY-MM-DD/YYYY-MM-DD_HHMMSS/"""
        parts = os.path.relpath(controller_per_run.run_directory, str(tmp_path)).split(os.sep)
        assert len(parts) == 2
        assert len(parts[0]) == 10   # YYYY-MM-DD
        assert len(parts[1]) == 17   # YYYY-MM-DD_HHMMSS

    def test_run_directory_exists(self, controller_per_run):
        assert os.path.isdir(controller_per_run.run_directory)

    def test_json_file_created(self, controller_per_run):
        assert os.path.exists(controller_per_run.json_file_path)

    def test_json_file_path_exposed(self, controller_per_run):
        assert controller_per_run.json_file_path != ""

    def test_log_directory_exposed(self, controller_per_run):
        assert controller_per_run.log_directory != ""

    def test_stream_handler_created(self, controller_per_run):
        assert controller_per_run.stream_handler is not None

    def test_stream_level_is_info(self, controller_per_run):
        assert controller_per_run.stream_handler.level == logging.INFO

    def test_readable_file_created(self, controller_per_run):
        assert os.path.exists(controller_per_run.readable_file_path)

    def test_json_handler_is_file_handler(self, controller_per_run):
        assert isinstance(controller_per_run.json_file_handler, logging.FileHandler)
        assert not isinstance(controller_per_run.json_file_handler, TimedRotatingFileHandler)


# ---------------------------------------------------------------------------
# DAILY_DIRECTORY
# ---------------------------------------------------------------------------

class TestDailyDirectory:

    def test_run_directory_is_daily_folder(self, controller_daily, tmp_path):
        """DAILY: run_directory should be tmp/YYYY-MM-DD/"""
        folder_name = os.path.basename(controller_daily.run_directory)
        assert len(folder_name) == 10
        assert folder_name.count("-") == 2

    def test_no_stream_handler(self, controller_daily):
        assert controller_daily.stream_handler is None

    def test_json_file_created(self, controller_daily):
        assert os.path.exists(controller_daily.json_file_path)

    def test_readable_file_created(self, controller_daily):
        assert os.path.exists(controller_daily.readable_file_path)


# ---------------------------------------------------------------------------
# BASIC_SINGLE_FILE
# ---------------------------------------------------------------------------

class TestBasicSingleFile:

    def test_run_directory_is_flat(self, controller_flat, tmp_path):
        assert os.path.normpath(controller_flat.run_directory) == os.path.normpath(str(tmp_path))

    def test_no_json_handler(self, controller_flat):
        assert controller_flat.json_file_handler is None
        assert controller_flat.json_file_path == ""

    def test_has_stream_handler(self, controller_flat):
        assert controller_flat.stream_handler is not None

    def test_stream_level_is_info(self, controller_flat):
        assert controller_flat.stream_handler.level == logging.INFO

    def test_readable_file_created(self, controller_flat):
        assert os.path.exists(controller_flat.readable_file_path)


# ---------------------------------------------------------------------------
# BASIC_JSON_FILE
# ---------------------------------------------------------------------------

class TestBasicJsonFile:

    def test_run_directory_is_flat(self, controller_json_file, tmp_path):
        assert os.path.normpath(controller_json_file.run_directory) == os.path.normpath(str(tmp_path))

    def test_no_readable_file_handler(self, controller_json_file):
        assert controller_json_file.readable_file_handler is None

    def test_json_file_created(self, controller_json_file):
        assert os.path.exists(controller_json_file.json_file_path)

    def test_has_stream_handler(self, controller_json_file):
        assert controller_json_file.stream_handler is not None


# ---------------------------------------------------------------------------
# BASIC_ROTATING_HANDLER
# ---------------------------------------------------------------------------

class TestBasicRotatingHandler:

    def test_run_directory_is_flat(self, controller_rotating, tmp_path):
        assert os.path.normpath(controller_rotating.run_directory) == os.path.normpath(str(tmp_path))

    def test_json_handler_is_timed_rotating(self, controller_rotating):
        assert isinstance(controller_rotating.json_file_handler, TimedRotatingFileHandler)

    def test_stream_level_is_warning(self, controller_rotating):
        assert controller_rotating.stream_handler is not None
        assert controller_rotating.stream_handler.level == logging.WARNING


# ---------------------------------------------------------------------------
# Mode stored on class
# ---------------------------------------------------------------------------

class TestModeAttribute:

    def test_mode_stored_on_class(self, tmp_path):
        hc = HandlerController(log_directory=str(tmp_path), mode=DAILY_DIRECTORY)
        assert HandlerController.mode == DAILY_DIRECTORY
