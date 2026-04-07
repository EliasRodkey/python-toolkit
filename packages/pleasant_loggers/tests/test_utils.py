"""
tests.test_utils

Tests for public file/directory utilities in _utils.py.
"""
import os
import shutil

import pytest

from pleasant_loggers._utils import (
    LOG_FILE_DEFAULT_DIRECTORY,
    _create_datestamp,
    _compose_global_run_id,
    get_log_directories,
    get_log_files,
    delete_log_directory,
    delete_todays_logs,
    clear_logs,
)

TEST_LOG_DIRECTORIES = {
    "test_logs_1": ["this_is_a_log_file.log", "this_is_a_json_log_file.json.log"],
    "more_log_files": ["another_log_file.log", "not_a_log_file.png"],
    _create_datestamp(): [
        f"{_compose_global_run_id('main')}.log",
        f"{_compose_global_run_id('thread_2')}.log",
        f"{_compose_global_run_id('json')}.json.log",
    ],
}


@pytest.fixture()
def test_logs():
    """Create a fake log directory structure before each test; clean up after."""
    try:
        for dir_name, files in TEST_LOG_DIRECTORIES.items():
            os.makedirs(os.path.join(LOG_FILE_DEFAULT_DIRECTORY, dir_name), exist_ok=True)
            for file in files:
                path = os.path.join(LOG_FILE_DEFAULT_DIRECTORY, dir_name, file)
                with open(path, "w", encoding="utf-8") as f:
                    f.write("Test log file")
        yield
    except Exception:
        raise
    finally:
        for dir_name in TEST_LOG_DIRECTORIES:
            path = os.path.join(LOG_FILE_DEFAULT_DIRECTORY, dir_name)
            if os.path.exists(path):
                shutil.rmtree(path)


def test_get_log_directories(test_logs):
    """get_log_directories() should return the created directories."""
    log_dirs = get_log_directories()
    for d in TEST_LOG_DIRECTORIES:
        assert d in log_dirs


def test_get_log_files(test_logs):
    """get_log_files() should list only .log files inside each directory."""
    log_files_dict = get_log_files()
    for dir_name, files in log_files_dict.items():
        assert dir_name in TEST_LOG_DIRECTORIES
        for f in files:
            assert f in TEST_LOG_DIRECTORIES[dir_name]


def test_delete_log_directory(test_logs):
    """delete_log_directory() should remove the named directory."""
    dir_to_delete = list(TEST_LOG_DIRECTORIES.keys())[0]
    delete_log_directory(dir_to_delete)
    assert dir_to_delete not in get_log_directories()


def test_delete_log_directory_not_exist(test_logs):
    """Deleting a non-existent directory should not raise an error."""
    delete_log_directory("not_a_real_dir")  # Should not raise


def test_delete_todays_logs(test_logs):
    """delete_todays_logs() should remove today's log directory."""
    today = _create_datestamp()
    delete_todays_logs()
    assert today not in get_log_directories()


def test_clear_logs(test_logs):
    """clear_logs() should remove all log directories."""
    clear_logs()
    assert get_log_directories() == []
