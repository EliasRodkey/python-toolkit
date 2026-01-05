#!python3
'''
local_db_handler

This package contains modules related to local database connection / creation / deletion / editing / etc.

Modules:
    - database_connections.py
    - database_file.py:
    - database_manager.py:
    - utils.py:
'''
# Metadata
__version__ = '0.2.1'
__author__ = 'Elias Rodkey'

# Configure logging settings
from loggers import Logger
from loggers import ELoggingFormats as ELF

# Package Level Constants
import os
DEFAULT_DB_DIRECTORY = os.path.join(os.getcwd(), 'data', 'dbs')

# Imports modules, functions, and classes for clean package interface
from .base_table import BaseTable, ESQLDataTypes
from .database_connections import create_engine_conn, create_session
from .database_file import DatabaseFile
from .database_manager import DatabaseManager
from .utils import check_db_exists, is_db_file

# Defines importable functions for package
__all__ = [
    'check_db_exists',
    'is_db_file',
    'create_engine_conn',
    'create_session',
    'DatabaseFile',
    'DatabaseManager',
    'BaseTable',
    'ESQLDataTypes'
]