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
from loggers import Logger
from loggers import ELoggingFormats as ELF

# Imports modules, functions, and classes for clean package interface
from .db_connections import create_db_session
from .database_file import DatabaseFile
from .utils import check_db_exists, is_db_file

# Defines importable functions for package
__all__ = [
    'check_db_exists',
    'is_db_file',
    'create_engine_conn',
    'create_session',
    'DatabaseFile',
    'LOGGERS'
]