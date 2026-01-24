"""
loggers.test_utils.py

Unit tests for utils.py using pytest.
"""
import pytest
import time
import os
import shutil

from loggers.utils import (
    LOG_FILE_DEFAULT_DIRECTORY, 
    create_datestamp,
    compose_global_run_id,
    get_log_directories, 
    get_log_files, 
    delete_log_directory, 
    delete_todays_logs, 
    clear_logs
    )

TEST_LOG_DIRECTORIES = {
    "test_logs_1": ["this_is_a_log_file.log", "this_is_a_json_log_file.json.log"], 
    "more_log_files": ["another_log_file.log", "not_a_log_file.png"], 
    create_datestamp(): [f"{compose_global_run_id('main')}.log", f"{compose_global_run_id('thread_2')}.log", f"{compose_global_run_id('json')}.json.log"]
    }

@pytest.fixture()
def test_logs():
    """Fixture to create fresh log file structure before each test"""
    
    try:
        # Setup: create log folders and files
        for dir, files in TEST_LOG_DIRECTORIES.items():
            os.makedirs(os.path.join(LOG_FILE_DEFAULT_DIRECTORY, dir), exist_ok=True)
        
            for i, file in enumerate(files):
                with open(os.path.join(LOG_FILE_DEFAULT_DIRECTORY, dir, file), "w", encoding="utf-8") as f:
                    f.write(f"Test log file")

        yield # Provide something to the test

    except Exception as e:
        print(e)
        raise

    finally:
        # Teardown: Ensure the session is closed and the files are deleted
        # pass
        for dir in TEST_LOG_DIRECTORIES:
            path = os.path.join(LOG_FILE_DEFAULT_DIRECTORY, dir)
            if os.path.exists(path):
                shutil.rmtree(path)


def test_get_log_directories(test_logs):
    """Tests the get_log_directories function by verifying they are correctly listed based on the setup"""
    log_dirs = get_log_directories()

    for dir in log_dirs:
        assert dir in TEST_LOG_DIRECTORIES


def test_get_log_files(test_logs):
    """Tests the get_log_files function verifying they are correctly listed based on the setup"""
    log_files_dict = get_log_files()

    for dir, files in log_files_dict.items():
        assert dir in TEST_LOG_DIRECTORIES
        for file in files:
            assert file in TEST_LOG_DIRECTORIES[dir]


def test_delete_log_directory(test_logs):
    """Tests the deletion of an existing log directory"""
    dir_to_delete = list(TEST_LOG_DIRECTORIES.keys())[0]

    delete_log_directory(dir_to_delete)
    remaining_dirs = get_log_directories()
    assert dir_to_delete not in remaining_dirs


def test_delete_log_directory_not_exist(test_logs):
    """Tests the deletion of a non existent log in directory doesn't cause errors"""
    dir_to_delete = "not_a_log_dir"

    try:
        delete_log_directory(dir_to_delete)
    except Exception as e:
        assert False, f"error encountered in test_delete_log_directory_not_exist: {e}"


def test_delete_todays_logs(test_logs):
    """Tests the deletion of todays log directory"""
    dir_to_delete = create_datestamp()

    delete_todays_logs()
    remaining_dirs = get_log_directories()
    assert dir_to_delete not in remaining_dirs
    

def test_clear_logs(test_logs):
    """Tests the deletion of all logs in log directory"""
    clear_logs()
    remaining_dirs = get_log_directories()

    assert remaining_dirs == []