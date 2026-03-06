#!python3
"""
This module contains a mock table object for testing purposes.

The MockTableObject class is used to simulate a database table for unit tests.
It inherits from the BaseTable class and defines a simple schema with columns
for id, name, age, and email.
"""

# Add current directory to path
import sys
sys.path.insert(0, ".")

# Standard library imports
from datetime import datetime, date

# Third-Party library imports
import pytest

# local imports
from local_db.base_table import BaseTable, ESQLDataTypes
import pandas as pd

# Constants
TEST_ENTRY_1 = {
    "name": "John Doe",
    "age": 30,
    "email": "john.doe@email.com"
}
TEST_ENTRY_2 = {
    "name": "Jane Doe",
    "age": 25,
    "email": "jane.doe@email.com"
}
TEST_ENTRY_3 = {
    "name": "Alice Smith",
    "age": 30,
    "email": "alice.smith@email.com"
}
INVALID_ENTRY = {
    "name": "Invalid Entry",
    "age": "not an integer",
    "email": 12345
}
INVALID_DF = pd.DataFrame({
    "id": ["one", "two", "three"],
    "name": [123, 456, 789],
    "age": ["thirty", "twenty-five", "forty"],
    "email": [True, False, None]
})

class MockTableObject(BaseTable):
    """A table object for testing purposes"""
    __tablename__ = "test_table"
    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    name = ESQLDataTypes.Column(ESQLDataTypes.String(50), nullable=False)
    age = ESQLDataTypes.Column(ESQLDataTypes.Integer)
    email = ESQLDataTypes.Column(ESQLDataTypes.String(100), unique=True)



DATE_ENTRY_1 = {
    "created_date": date(2024, 1, 1),
    "accessed_timestamp": datetime(2024, 1, 5, 12),
    "name": "John"
}
DATE_ENTRY_2 = {
    "created_date": date(2024, 2, 5),
    "accessed_timestamp": datetime(2024, 2, 10, 5),
    "name": "Mimi"
}
DATE_ENTRY_3 = {
    "created_date": date(2024, 3, 14),
    "accessed_timestamp": datetime(2024, 3, 21, 16),
    "name": "Gia"
}
SWITCHED_DATE_ENTRY = {
    "created_date": datetime(2024, 11, 13, 1),
    "accessed_timestamp": date(2024, 12, 25),
    "name": "Eli"
}

class DatetimeMockTableObject(BaseTable):
    """A table object for testing purposes"""
    __tablename__ = "datetime_test_table"
    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    created_date = ESQLDataTypes.Column(ESQLDataTypes.Date, nullable=False)
    accessed_timestamp = ESQLDataTypes.Column(ESQLDataTypes.DateTime)
    name = ESQLDataTypes.Column(ESQLDataTypes.String(100), unique=True)