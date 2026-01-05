'''
local_db.base_table.py
This module defines a base table class using SQLAlchemy's declarative base. 
It provides a foundation for creating database models and includes utility 
functions to retrieve column names and their corresponding types.

Classes:
    Base: The declarative base class for all database models.
    BaseTable: An abstract base class for database tables with utility methods.
'''
from enum import Enum
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


class ESQLDataTypes(Enum):
    """An Enum class containing all of the SQL datatypes available through sqlalchemy"""
    Column = Column # SQLalchemy column class
    Integer = Integer  # Integer type
    String = String  # String type with optional length
    Float = Float # Floating-point number
    Boolean = Boolean  # Boolean type (True/False)
    Date = Date  # Date type (year, month, day)
    DateTime = DateTime  # Date and time type
    Time = Time  # Time type (hour, minute, second)
    Text = Text  # Large text field
    LargeBinary = LargeBinary  # Binary data (e.g., files, images)
    JSON = JSON  # JSON-encoded data
    Enum = Enum  # Enumerated type with fixed values
    Numeric = Numeric  # Fixed-precision number
    SmallInteger = SmallInteger  # Smaller integer type
    BigInteger = BigInteger  # Larger integer type
    Interval = Interval  # Time interval
    Unicode = Unicode  # Unicode string
    UnicodeText = UnicodeText  # Large Unicode text field
    PickleType = PickleType  # Stores Python objects serialized via pickle
    UUID = UUID  # Universally unique identifier
    ARRAY = ARRAY  # Array type (PostgreSQL-specific)


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
        '''Returns a list of column names for the model.'''
        return [column.name for column in cls.__table__.columns]


    @classmethod
    def get_column_types(cls):
        '''Returns a dictionary mapping column names to their types.'''
        return {column.name: type(column.type) for column in cls.__table__.columns}
    

    @property
    def column_names(self):
        '''Returns a list of column names for the instance.'''
        return self.get_column_names()
    

    @property
    def column_types(self):
        '''Returns a dictionary mapping column names to their types for the instance.'''
        return self.get_column_types()
