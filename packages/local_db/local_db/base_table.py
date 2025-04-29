'''
This module defines a base table class using SQLAlchemy's declarative base. 
It provides a foundation for creating database models and includes utility 
functions to retrieve column names and their corresponding types.

Classes:
    Base: The declarative base class for all database models.
    
Functions:
    get_column_names(): Retrieves a list of column names for the table.
    get_column_types(): Retrieves a dictionary mapping column names to their data types.
'''

from sqlalchemy.orm import declarative_base

Base = declarative_base()

class BaseTable(Base):
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