"""
local_db.base_table.py
This module defines a base table class using SQLAlchemy"s declarative base. 
It provides a foundation for creating database models and includes utility 
functions to retrieve column names and their corresponding types.

Classes:
    Base: The declarative base class for all database models.
    BaseTable: An abstract base class for database tables with utility methods.
"""

# Standard library imports
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
import re
from typing import Any
import uuid

from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,  # Defines a column in a table
    UniqueConstraint, # Ensures unique values in specified columns
    Integer,  # Integer type
    String,  # String type with optional length
    Float,  # Floating-point number
    Boolean,  # Boolean type (True/False)
    Date,  # Date type (year, month, day)
    DateTime,  # Date and time type
    Time,  # Time type (hour, minute, second)
    Text,  # Large text field
    LargeBinary,  # Binary data (e.g., files, images)
    JSON,  # JSON-encoded data
    Enum,  # Enumerated type with fixed values
    Numeric,  # Fixed-precision number
    SmallInteger,  # Smaller integer type
    BigInteger,  # Larger integer type
    Interval,  # Time interval
    Unicode,  # Unicode string
    UnicodeText,  # Large Unicode text field
    PickleType,  # Stores Python objects serialized via pickle
    UUID,  # Universally unique identifier
    ARRAY,  # Array type (PostgreSQL-specific)
)

SQLA_TYPE_MAP = {
    Integer: int,
    String: str,
    Float: float,
    Boolean: bool,
    Date: date,
    DateTime: datetime,
    Time: time,
    Text: str,
    LargeBinary: bytes,
    JSON: dict,
    Enum: Enum,
    Numeric: Decimal,
    SmallInteger: int,
    BigInteger: int,
    Interval: timedelta,
    Unicode: str,
    UnicodeText: str,
    PickleType: Any,
    UUID: uuid.UUID,
    ARRAY: list,
}

Base = declarative_base()



class BaseTable(Base):
    """
    Abstract base class for database tables.
    
    properties:
        - column_names: Returns a list of column names for the model.
        - column_types: Returns a dictionary mapping column names to their types.
    """
    __abstract__ = True  # Prevents SQLAlchemy from creating a table for this class

    @classmethod
    def get_column_names(cls):
        """Returns a list of column names for the model."""
        return [column.name for column in cls.__table__.columns]


    @classmethod
    def get_column_sqla_types(cls):
        """Returns a dictionary mapping column names to their types."""
        return {column.name: type(column.type) for column in cls.__table__.columns}
    
    @classmethod
    def get_column_python_types(cls):
        """Returns a dictionary mapping column names to their types."""
        return {column.name: SQLA_TYPE_MAP[type(column.type)] for column in cls.__table__.columns}
    
    @property
    def column_names(self):
        """Returns a list of column names for the instance."""
        return self.get_column_names()

    @property
    def column_types(self):
        """Returns a dictionary mapping column names to their types for the instance."""
        return self.get_column_sqla_types()



class DatabaseIntegrityError(Exception):
    def __init__(self, orig: Exception, table: "BaseTable"):
        self.table_name = table.__tablename__
        self.message = str(orig.orig)
        match = re.search(r"UNIQUE constraint failed: \w+\.(\w+)", self.message)
        self.column = match.group(1) if match else None
        detail = f", column: {self.column}" if self.column else ""
        super().__init__(f"Database integrity error in {self.table_name}{detail}. {self.message}")



class ItemNotFoundError(Exception):
    def __init__(self, item_id, table: BaseTable, message: str="Item not found in database:"):
        self.item_id = item_id
        self.table_name = table.__tablename__
        self.message = f"{message} {self.table_name}, id: {item_id}"
        super().__init__(self.message)