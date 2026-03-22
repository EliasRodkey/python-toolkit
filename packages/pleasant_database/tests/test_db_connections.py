#!python3
"""
tests.test_db_connections.py

This module contains tests for functions in the database_connections.py module.

Functions:
    - test_db_conn: Tests the create_engine_conn() function by attempting to create a connection engine object to a local database URL.
"""

# Add current directory to path
import sys
sys.path.insert(0, ".")


from sqlalchemy.exc import OperationalError

# local imports
from local_db.database_connections import create_engine_conn, create_session


# Constants
TEST_URL = "data\\test.db"


# Functions
def test_db_conn():
    """Tests the create_engine_conn() function from db_connections by creating an engine with a test db"""
    try:
        # attempt to connect to a database URl using SQLalchemy engine and session
        engine = create_engine_conn(TEST_URL)
        Session = create_session(engine)
        assert True

    except OperationalError as e:
        # Fail on SQLalchemy OperationalError
        assert False, f"Database connection failed: {e}"

    finally:
        # Close open db connection
        Session.close()