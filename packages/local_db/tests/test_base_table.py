#!python3
'''
tests.db_file_handler_test.py

this module contains tests for functions contained in the db__file_handler.py module

Funciton:
    create():
    - test_create_database: attempts to create a db file in a directory from a relative path

    DatabaseFile.move()
    - test_move_db_default: attempt to move a db file from a default location (cwd) to a default location (.\\data) 
    - test_move_db_custom_1: attempt to move a db file from a default location to a custom location (.\\data)
    - test_move_db_custom_2: attempt to move a db file from a custom location (cwd) to a default location (.\\data)
    - test_move_db_custom_3: attempt to move a db file from a custom location to a custom location (.\\data)
    - test_move_db_not_exist: attempt to move a db file that doesn't exist
    - test_move_db_target_exist: attempt to move a db file that already exists at target location

    delete_db()
    - test_delete_db_not_exist: attempts to delete a db file that does not exist
    - test_delete_db: attempts to delete a db file that does exist
    - test_delete_db_multiple: attempts to delete a db file that has multiple copies under one directory
'''

# Add current directory to path
import sys
sys.path.insert(0, '.')


# Standard library imports
import os
import random

# Third-Party library imports
import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

# local imports
from local_db import DEFAULT_DB_DIRECTORY
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



class MockTableObject(BaseTable):
    '''A table object for testing purposes'''
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer)
    email = Column(String(100))



class TestBaseTable:
    '''Tests the BaseTable class from base_table.py'''

    def test_class_column_names(self):
        '''Tests the get_column_names() method of the BaseTable class'''
        columns = MockTableObject.get_column_names()
        assert columns == ['id', 'name', 'age', 'email'], f'Expected ["id", "name", "age", "email"], but got {columns}'

    def test_class_column_types(self):
        '''Tests the get_column_types() method of the BaseTable class'''
        column_types = MockTableObject.get_column_types()
        assert column_types == {'id': Integer, 'name': String, 'age': Integer, 'email': String}, f'Expected {{\'id\': Integer, \'name\': String, \'age\': Integer, \'email\': String}}, but got {column_types}'