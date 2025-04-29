#!python3
'''
tests.test_base_table.py

This module contains tests for the BaseTable class and its methods.

Functions:
    TestBaseTable:
    - test_class_column_names: Tests the get_column_names() method of the BaseTable class.
    - test_class_column_types: Tests the get_column_types() method of the BaseTable class.
    - test_instance_column_names: Tests the column_names property of the BaseTable class.
    - test_instance_column_types: Tests the column_types property of the BaseTable class.
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
from .mock_table_object import MockTableObject, TEST_ENTRY_1



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
    

    def test_instance_column_names(self):
        '''Tests the column_names property of the BaseTable class'''
        instance = MockTableObject(**TEST_ENTRY_1)
        columns = instance.column_names
        assert columns == ['id', 'name', 'age', 'email'], f'Expected ["id", "name", "age", "email"], but got {columns}'


    def test_instance_column_types(self):
        '''Tests the column_types property of the BaseTable class'''
        instance = MockTableObject(**TEST_ENTRY_1)
        column_types = instance.column_types
        assert column_types == {'id': Integer, 'name': String, 'age': Integer, 'email': String}, f'Expected {{\'id\': Integer, \'name\': String, \'age\': Integer, \'email\': String}}, but got {column_types}'