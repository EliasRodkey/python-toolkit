#!python3
'''
local_db_handler.database_manader.py

This module contains a database object class

Classes:
    - LocalDB: a class object which allows for the following actions to be performed:
        - Creation
        - Reading
        - Editing
        - Updating
        - Deletion

    - LocalDB functions:
        - 
'''

# Initiate module logger
from . import Logger, ELF

# Third-Party library imports
# import pandas as pd

# local imports
from local_db.database_connections import create_engine_conn, create_session
from local_db.database_file import DatabaseFile
from local_db.utils import os


# Initialize module logger
_logger = Logger('database_manager')
_logger.add_file_handler(format=ELF.FORMAT_LOGGER_NAME)



class DatabaseManager():
    '''
    Generic database manager wrapper class that allows for simple database operations to be performed on a local database file.
    '''

    def __init__(self, database_obj_class, database_file: DatabaseFile):
        '''
        Initializes the DatabaseManager with a SQLAlchemy session and a database object class.

        Args:
            database_file (DatabaseFile): The DatabaseFile object representing the database file.
            database_obj_class (class): The SQLAlchemy ORM class representing the database table. (class not instance)
        '''

        # Initialize the database file and object class
        self.file = database_file
        self.database_obj_class = database_obj_class
        
        # Create database session using DatabaseFile file_path attribute
        self.engine = create_engine_conn(os.path.join(self.file.file_path))
        self.database_obj_class.metadata.create_all(self.engine)
        self.session = create_session(self.engine)

        _logger.info(f'DatabaseManager connection initialized with file: {self.file.name}')
        _logger.debug(f'DatabaseManager -> connection initialized with file {self.file.abspath} and object class type: {self.database_obj_class}')
        

    def add_item(self, **kwargs):
        '''
        Adds a new item to the database. unpack a dictionary if attributes using '**' operator

        Args:
            **kwargs: Keyword arguments representing the attributes of the item to be added.
        '''
        # Create a new instance of the database object class with the provided attributes
        new_item = self.database_obj_class(kwargs)

        # Add the new item to the session and commit the changes to the database
        self.session.add(new_item)
        self.session.commit()
        return new_item


    def fetch_all_items(self):
        '''
        Fetches all items from the database table
        
        Returns:
            list: A list of all items in the database table.
        '''
        return self.session.query(self.database_obj_class).all()
    

    def fetch_item_by_id(self, item_id):
        '''
        Fetches an item from the database based on its ID.
        
        Args:
            item_id (int): The ID of the item to be fetched.

        Returns:
            item: The item object if found, otherwise None.
        '''

        # Locate the item in the database using its ID
        item = self.session.query(self.database_obj_class).filter_by(id=item_id).first()

        # If the item exists, return it; otherwise, return None
        if item:
            return item
        else:
            return None
    
    def fetch_items_by_attribute(self, **kwargs):
        '''
        Fetches items from the database based on specified attributes.
        
        Args:
            **kwargs: Keyword arguments representing the attributes to filter by.

        Returns:
            list: A list of items matching the specified attributes.
        '''

        # Create a query object to filter items based on the provided attributes
        query = self.session.query(self.database_obj_class).filter_by(**kwargs)

        if query:
            # If the query returns results, return them as a list
            return query.all()
        else:
            # If no results are found, return an empty list
            return []


    def delete_item(self, item_id):
        '''
        Deletes an item from the database based on its ID.
        
        Args:
            item_id (int): The ID of the item to be deleted.
        '''

        # Locate the item in the database using its ID
        item = self.session.query(self.database_obj_class).filter_by(id=item_id).first()

        # If the item exists, delete it from the session and commit the changes to the database
        if item:
            self.session.delete(item)
            self.session.commit()


    def update_item(self, item_id, **kwargs):
        '''
        Updates an item in the database based on its ID.

        Args:
            item_id (int): The ID of the item to be updated.
            **kwargs: Keyword arguments representing the attributes to be updated.
        '''

        # Locate the item in the database using its ID
        item = self.session.query(self.database_obj_class).filter_by(id=item_id).first()

        # If the item exists, update its attributes and commit the changes to the database
        if item:
            # Unpack the keyword arguments and update the item's attributes
            for key, value in kwargs.items():
                if hasattr(item, key): # Check if the attribute exists in the item
                    setattr(item, key, value)

            # Commit the changes to the database
            self.session.commit()


if __name__ == "__main__":
    pass