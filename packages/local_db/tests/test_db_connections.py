#!python3
'''
tests.db_connections_test.py

this module contains tests for functions contained in the db_connections.py module

Funciton:
    - test_create_engine_conn: atempts to create a connection engine object to a local URL
    - test_create_sesstion:
'''

# Add current directory to path
import sys
sys.path.insert(0, '.')

# Standard library imports
import os

# Third-Party library imports
import pytest
from sqlalchemy.exc import OperationalError

# local imports
from local_db_handler.db_connections import create_engine_conn, create_session


# Constants
TEST_URL = 'data\\test.db'


# Functions
def test_db_conn():
    '''Tests the create_engine_conn() function from db_connections by creating an engine with a test db'''
    try:
        # attempt to connect to a database URl using SQLalchemy engine and session
        engine = create_engine_conn(TEST_URL)
        Session = create_session(engine)
        assert True

    except OperationalError as e:
        # Fail on SQLalchemy OperationalError
        assert False, f'Database connection failed: {e}'

    finally:
        # Close open db connection
        Session.close()