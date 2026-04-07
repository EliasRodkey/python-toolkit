#!python3
"""
tests.test_base_table.py

This module contains tests for the BaseTable class and its methods.

Functions:
    TestBaseTable:
    - test_class_column_names: Tests the get_column_names() method of the BaseTable class.
    - test_class_column_types: Tests the get_column_types() method of the BaseTable class.
    - test_instance_column_names: Tests the column_names property of the BaseTable class.
    - test_instance_column_types: Tests the column_types property of the BaseTable class.
"""

# Add current directory to path
import sys
sys.path.insert(0, ".")


# Standard library imports
import os
import random

# Third-Party library imports
import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

# local imports
from pleasant_database.base_table import DatabaseIntegrityError, ItemNotFoundError
from sqlalchemy.exc import IntegrityError
from .mock_table_object import MockTableObject, TEST_ENTRY_1



class TestBaseTable:
    """Tests the BaseTable class from base_table.py"""

    def test_class_column_names(self):
        """Tests the get_column_names() method of the BaseTable class"""
        columns = MockTableObject.get_column_names()
        assert columns == ["id", "name", "age", "email"], f"Expected ['id', 'name', 'age', 'email'], but got {columns}"


    def test_class_column_types(self):
        """Tests the get_column_types() method of the BaseTable class"""
        column_types = MockTableObject.get_column_sqla_types()
        assert column_types == {"id": Integer, "name": String, "age": Integer, "email": String}, f"Expected {{\"id\": Integer, \"name\": String, \"age\": Integer, \"email\": String}}, but got {column_types}"
    

    def test_instance_column_names(self):
        """Tests the column_names property of the BaseTable class"""
        instance = MockTableObject(**TEST_ENTRY_1)
        columns = instance.column_names
        assert columns == ["id", "name", "age", "email"], f"Expected ['id', 'name', 'age', 'email'], but got {columns}"


    def test_instance_column_types(self):
        """Tests the column_types property of the BaseTable class"""
        instance = MockTableObject(**TEST_ENTRY_1)
        column_types = instance.column_types
        assert column_types == {"id": Integer, "name": String, "age": Integer, "email": String}, f"Expected {{\"id\": Integer, \"name\": String, \"age\": Integer, \"email\": String}}, but got {column_types}"


    def test_class_column_python_types(self):
        """Tests the get_column_python_types() class method of the BaseTable class"""
        python_types = MockTableObject.get_column_python_types()
        assert python_types == {"id": int, "name": str, "age": int, "email": str}, f"Got {python_types}"


class TestDatabaseIntegrityError:
    """Tests the DatabaseIntegrityError exception class"""

    def _make_integrity_error(self, message: str) -> DatabaseIntegrityError:
        """Helper: builds a DatabaseIntegrityError from a raw message string."""
        mock_orig = Exception(message)
        mock_sqla_error = IntegrityError(statement=None, params=None, orig=mock_orig)
        return DatabaseIntegrityError(mock_sqla_error, MockTableObject)

    def test_integrity_error_attributes(self):
        """DatabaseIntegrityError parses a UNIQUE constraint message correctly"""
        exc = self._make_integrity_error("UNIQUE constraint failed: test_table.email")
        assert exc.table_name == "test_table"
        assert exc.column == "email"
        assert "email" in str(exc)

    def test_integrity_error_no_column_match(self):
        """DatabaseIntegrityError sets column=None when the message has no UNIQUE constraint pattern"""
        exc = self._make_integrity_error("some other database error")
        assert exc.column is None
        assert exc.table_name == "test_table"


class TestItemNotFoundError:
    """Tests the ItemNotFoundError exception class"""

    def test_item_not_found_attributes(self):
        """ItemNotFoundError stores item_id, table_name, and includes both in its message"""
        exc = ItemNotFoundError(42, MockTableObject)
        assert exc.item_id == 42
        assert exc.table_name == "test_table"
        assert "test_table" in str(exc)
        assert "42" in str(exc)

    def test_item_not_found_custom_message(self):
        """ItemNotFoundError accepts a custom message prefix"""
        exc = ItemNotFoundError(7, MockTableObject, message="Not here:")
        assert exc.message.startswith("Not here:")