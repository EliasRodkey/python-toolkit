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
from sqlalchemy import Column, Integer, String

# local imports
from local_db.base_table import BaseTable


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


class MockTableObject(BaseTable):
    '''A table object for testing purposes'''
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer)
    email = Column(String(100))