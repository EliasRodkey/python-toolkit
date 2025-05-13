#!python3
'''
This module contains a mock table object for testing purposes.

The MockTableObject class is used to simulate a database table for unit tests.
It inherits from the BaseTable class and defines a simple schema with columns
for id, name, age, and email.
'''

# Add current directory to path
import sys
sys.path.insert(0, '.')


# Third-Party library imports
import pytest

# local imports
from local_db.base_table import BaseTable, ESQLDataTypes
import pandas as pd


# Constants
TEST_ENTRY_1 = {
    'name': 'John Doe',
    'age': 30,
    'email': 'john.doe@email.com'
}
TEST_ENTRY_2 = {
    'name': 'Jane Doe',
    'age': 25,
    'email': 'jane.doe@email.com'
}
TEST_ENTRY_3 = {
    'name': 'Alice Smith',
    'age': 30,
    'email': 'alice.smith@email.com'
}
INVALID_ENTRY = {
    'name': 'Invalid Entry',
    'age': 'not an integer',
    'email': 12345
}
INVALID_DF = pd.DataFrame({
    'id': ['one', 'two', 'three'],
    'name': [123, 456, 789],
    'age': ['thirty', 'twenty-five', 'forty'],
    'email': [True, False, None]
})

class MockTableObject(BaseTable):
    '''A table object for testing purposes'''
    __tablename__ = 'test_table'
    id = ESQLDataTypes.Column(ESQLDataTypes.Integer, primary_key=True, autoincrement=True)
    name = ESQLDataTypes.Column(ESQLDataTypes.String(50), nullable=False)
    age = ESQLDataTypes.Column(ESQLDataTypes.Integer)
    email = ESQLDataTypes.Column(ESQLDataTypes.String(100), unique=True)