#!python3
'''
local_db_handler

This package contains modules related to local database connection / creation / deletion / editing / etc.

Modules:
    - db_connections.py
    - db_file_handler.py:
    - local_db.py:
    - utils.py:
'''
# Metadata
__version__ = '0.2.0'
__author__ = 'Elias Rodkey'

# Configure logging settings
import logging
import logging.config

# Pull logging configuration from 'logging.conf'
logging.config.fileConfig('logging.conf')

# Imports modules, functions, and classes for clean package interface
from .db_connections import create_engine_conn, create_session, logger_db_connections
from .database_file import DatabaseFile, logger_database_file
from .utils import check_db_exists, is_db_file, logger_utils

LOGGERS = {
    'db_connections' : logger_db_connections,
    'database_file' : logger_database_file,
    'utils' : logger_utils
}

# Defines importable functions for package
__all__ = [
    'check_db_exists',
    'is_db_file',
    'create_engine_conn',
    'create_session',
    'DatabaseFile',
    'LOGGERS'
]


# optional lightweight initialization logic
