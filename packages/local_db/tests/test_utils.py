#!python3
'''
tests.utils_test.py

This module contains tests for functions contained in the utils.py module.

Functions:
    check_db_exists():
    - test_check_db_exists: verifies check_db_exists correctly identifies an existing database file.
    - test_check_db_not_exists: verifies check_db_exists correctly identifies a non-existing database file.

    is_db_file():
    - test_is_db_file_true: verifies is_db_file correctly identifies valid .db filenames.
    - test_is_db_file_false: verifies is_db_file correctly identifies invalid .db filenames or non-string inputs.
'''

# Add current directory to path
import sys
sys.path.insert(0, '.')


# Standard library imports
import os
import pandas as pd
import sqlite3

# Third-Party library imports
import pytest

# local imports
from local_db.utils import check_db_exists, is_db_file, map_dtype_to_sql, map_dtype_list_to_sql
from local_db.utils import Integer, Float, String, Boolean, DateTime, LargeBinary


# Constants
TEST_DB = 'test.db'
FAKE_DB = 'fake.db'
TEST_DB_DIR = os.path.join(os.getcwd(), 'data')
TEST_DB_PATH = os.path.join(TEST_DB_DIR, TEST_DB)
CUSTOM_TEST_DB_DIR = os.path.join(TEST_DB_DIR, 'logs')
CUSTOM_TEST_DB_PATH = os.path.join(CUSTOM_TEST_DB_DIR, TEST_DB)


# Functions
def test_check_db_exists():
    '''Tests the check_db_exists() function from utils by feeding it a db file that exists'''
    # Create db file
    sqlite3.connect(TEST_DB_PATH).close()

    # Check if db exists in data directory
    assert check_db_exists(TEST_DB, TEST_DB_DIR)

    # Delete db file
    os.remove(TEST_DB_PATH)
    assert not check_db_exists(TEST_DB, TEST_DB_DIR)


def test_check_db_not_exists():
    '''Tests the check_db_exists() function from utils by feeding it a db file that does not exists''' 
    assert not check_db_exists(FAKE_DB, CUSTOM_TEST_DB_DIR)


# Pytest parameters for True db file test
@pytest.mark.parametrize('filename', [
    ('test.db'),
    (TEST_DB_PATH),
    ('asdfghjkl.db'),
])
def test_is_db_file_true(filename:str):
    '''Checks to see if is_db_file function from utils is properly identifying .db strings'''
    assert is_db_file(filename)

# Pytest parameters for False db file test
@pytest.mark.parametrize('filename', [
    ('test.db1'),
    (CUSTOM_TEST_DB_DIR),
    ('.dbs'),
    (5),
    (3.14),
    ([]),
    (dict),
])
def test_is_db_file_false(filename:str):
    '''Checks to see if is_db_file function from utils is properly identifying .db strings'''
    assert not is_db_file(filename)


# TODO:Add a test for large binary data types
@pytest.mark.parametrize('dtype, expected', [
    (pd.Series([1, 2, 3]).dtype, Integer),
    (pd.Series([1.1, 2.2, 3.3]).dtype, Float),
    (pd.Series([True, False, True]).dtype, Boolean),
    (pd.Series(['2023-01-01', '2023-01-02']).astype('datetime64[ns]').dtype, DateTime),
    (pd.Series(['a', 'b', 'c']).dtype, String),
    (pd.Series([b'bytes', b'data']).dtype, String),
])
def test_map_dtype_to_sql(dtype, expected):
    '''Tests the map_dtype_to_sql function from utils by checking if it correctly maps data types to SQLAlchemy types'''
    assert map_dtype_to_sql(dtype) == expected