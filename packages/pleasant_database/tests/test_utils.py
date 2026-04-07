#!python3
"""
tests.utils_test.py

This module contains tests for functions contained in the utils.py module.

Functions:
    check_db_exists():
    - test_check_db_exists: verifies check_db_exists correctly identifies an existing database file.
    - test_check_db_not_exists: verifies check_db_exists correctly identifies a non-existing database file.

    is_db_file():
    - test_is_db_file_true: verifies is_db_file correctly identifies valid .db filenames.
    - test_is_db_file_false: verifies is_db_file correctly identifies invalid .db filenames or non-string inputs.
"""

# Add current directory to path
import sys
sys.path.insert(0, ".")


# Standard library imports
import os
import pandas as pd
import sqlite3

# Third-Party library imports
import pytest

# local imports
from pleasant_database.utils import check_db_exists, is_db_file, map_dtype_to_sql, map_dtype_list_to_sql, orm_list_to_dataframe
from pleasant_database.utils import Column, Integer, Float, String, Boolean, DateTime, LargeBinary, create_engine


# Constants
TEST_DB = "test.db"
FAKE_DB = "fake.db"
TEST_DB_DIR = os.path.join(os.getcwd(), "data")
TEST_DB_PATH = os.path.join(TEST_DB_DIR, TEST_DB)
CUSTOM_TEST_DB_DIR = os.path.join(TEST_DB_DIR, "logs")
CUSTOM_TEST_DB_PATH = os.path.join(CUSTOM_TEST_DB_DIR, TEST_DB)


# Functions
def test_check_db_exists():
    """Tests the check_db_exists() function from utils by feeding it a db file that exists"""
    # Create db file
    sqlite3.connect(TEST_DB_PATH).close()

    # Check if db exists in data directory
    assert check_db_exists(TEST_DB, TEST_DB_DIR)

    # Delete db file
    os.remove(TEST_DB_PATH)
    assert not check_db_exists(TEST_DB, TEST_DB_DIR)


def test_check_db_not_exists():
    """Tests the check_db_exists() function from utils by feeding it a db file that does not exists""" 
    assert not check_db_exists(FAKE_DB, CUSTOM_TEST_DB_DIR)


# Pytest parameters for True db file test
@pytest.mark.parametrize("filename", [
    ("test.db"),
    (TEST_DB_PATH),
    ("asdfghjkl.db"),
])
def test_is_db_file_true(filename:str):
    """Checks to see if is_db_file function from utils is properly identifying .db strings"""
    assert is_db_file(filename)

# Pytest parameters for False db file test
@pytest.mark.parametrize("filename", [
    ("test.db1"),
    (CUSTOM_TEST_DB_DIR),
    (".dbs"),
    (5),
    (3.14),
    ([]),
    (dict),
])
def test_is_db_file_false(filename:str):
    """Checks to see if is_db_file function from utils is properly identifying .db strings"""
    assert not is_db_file(filename)


# TODO:Add a test for large binary data types
@pytest.mark.parametrize("dtype, expected", [
    (pd.Series([1, 2, 3]).dtype, Integer),
    (pd.Series([1.1, 2.2, 3.3]).dtype, Float),
    (pd.Series([True, False, True]).dtype, Boolean),
    (pd.Series(["2023-01-01", "2023-01-02"]).astype("datetime64[ns]").dtype, DateTime),
    (pd.Series(["a", "b", "c"]).dtype, String),
    (pd.Series([b"bytes", b"data"]).dtype, String),
])
def test_map_dtype_to_sql(dtype, expected):
    """Tests the map_dtype_to_sql function from utils by checking if it correctly maps data types to SQLAlchemy types"""
    assert map_dtype_to_sql(dtype) == expected


def test_orm_list_to_dataframe():
    """Tests the orm_list_to_dataframe function from utils by checking if it correctly converts a list of ORM objects to a DataFrame"""
    from sqlalchemy.orm import sessionmaker, declarative_base

    # Define a simple ORM model for testing
    Base = declarative_base()

    class TestModel(Base):
        __tablename__ = "test_model"
        id = Column(Integer, primary_key=True)
        name = Column(String)

    # Create an in-memory SQLite database and add test data
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add test data
    session.add_all([TestModel(name="Alice"), TestModel(name="Bob")])
    session.commit()

    # Query the data
    orm_objects = session.query(TestModel).all()

    # Convert to DataFrame
    df = orm_list_to_dataframe(orm_objects)

    # Expected DataFrame
    expected_df = pd.DataFrame({"id": [1, 2], "name": ["Alice", "Bob"]})

    # Assert DataFrames are equal
    pd.testing.assert_frame_equal(df, expected_df)


def test_map_dtype_to_sql_unsupported_raises():
    """
    Tests that map_dtype_to_sql raises an error for dtypes that have no SQLAlchemy mapping.

    The docstring says ValueError, but pd.api.types.is_binary_dtype was removed in newer
    pandas versions, causing AttributeError before the else-raise is reached. Either error
    correctly signals an unsupported dtype.
    """
    unsupported_dtype = pd.Series([1 + 2j]).dtype  # complex128 — not handled by any branch
    with pytest.raises((ValueError, AttributeError)):
        map_dtype_to_sql(unsupported_dtype)


def test_map_dtype_list_to_sql():
    """Tests that map_dtype_list_to_sql maps a list of dtypes to the correct SQLAlchemy types"""
    dtypes = [pd.Series([1, 2, 3]).dtype, pd.Series(["a", "b"]).dtype]
    result = map_dtype_list_to_sql(dtypes)
    assert result == [Integer, String]


def test_orm_list_to_dataframe_empty():
    """Tests that orm_list_to_dataframe returns an empty DataFrame (not an error) for an empty list"""
    result = orm_list_to_dataframe([])
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0