"""
pleasant_loggers._utils

File/directory utilities (public) and timestamp helpers (private).
"""
from datetime import datetime
import os
import shutil


# ---------------------------------------------------------------------------
# Private timestamp helpers (used internally by _handlers.py)
# ---------------------------------------------------------------------------

LOG_FILE_DEFAULT_DIRECTORY: str = os.path.join("data", "logs")


def _create_datestamp() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def _create_timestamp() -> str:
    """Return the current time as HHMMSS."""
    return datetime.now().strftime("%H%M%S")


def _create_log_datetime_stamp() -> str:
    """Return a combined datetime stamp: YYYY-MM-DD_HHMMSS."""
    return f"{_create_datestamp()}_{_create_timestamp()}"


def _compose_global_run_id(run_name: str) -> str:
    """Return a unique run ID combining the datetime stamp and run_name."""
    return f"{_create_log_datetime_stamp()}_{run_name}"


# ---------------------------------------------------------------------------
# Public file/directory utilities
# ---------------------------------------------------------------------------

def get_log_directories(default_log_directory: str = LOG_FILE_DEFAULT_DIRECTORY) -> list[str]:
    """Return directory names inside the given log directory."""
    contents = os.listdir(default_log_directory)
    return [d for d in contents if os.path.isdir(os.path.join(default_log_directory, d))]


def get_log_files(default_log_directory: str = LOG_FILE_DEFAULT_DIRECTORY) -> dict[str, list[str]]:
    """
    Return a dict mapping each daily log folder name to a list of .log file names
    found inside it.
    """
    log_file_dict: dict[str, list[str]] = {}
    for d in get_log_directories(default_log_directory):
        dir_path = os.path.join(default_log_directory, d)
        log_file_dict[d] = [
            f for f in os.listdir(dir_path) if f.endswith(".log")
        ]
    return log_file_dict


def delete_log_directory(
    directory_name: str,
    default_log_directory: str = LOG_FILE_DEFAULT_DIRECTORY,
) -> None:
    """Delete the named directory (and all contents) inside the log directory."""
    path = os.path.join(os.getcwd(), default_log_directory, directory_name)
    if os.path.exists(path):
        shutil.rmtree(path)


def delete_todays_logs(default_log_directory: str = LOG_FILE_DEFAULT_DIRECTORY) -> None:
    """Delete the directory that contains today's logs."""
    delete_log_directory(_create_datestamp(), default_log_directory=default_log_directory)


def clear_logs(default_log_directory: str = LOG_FILE_DEFAULT_DIRECTORY) -> None:
    """Delete all log directories inside the log directory."""
    for d in get_log_directories(default_log_directory):
        delete_log_directory(d, default_log_directory=default_log_directory)
