#!python3
'''
tests.utils_test.py

this module contains tests for functions contained in the utils.py module

Funciton:
    check_db_exists():
    - test_check_db_exists: attempts to check for a database that does exist
    - test_check_db_not_exists: attempts to check for a database that does not exist

    is_db_file():
    - test_is_db_file_true: checks example db filenames that should return True
    - test_is_db_file_false: checks examples db filenames that should return False
'''

# Add current directory to path
import sys
sys.path.insert(0, '.')

# Standard library imports
import os
import sqlite3

# Third-Party library imports
import pytest

# local imports
from local_db.utils import check_db_exists, is_db_file


# Constants
TEST_DB = 'test.db'
FAKE_DB = 'fake.db'
TEST_DB_DIR = os.path.join(os.curdir, 'data')
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