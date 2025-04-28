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
from .db_connections import create_engine_conn, create_session
from .database_file import create_db, move_db, delete_db
from .utils import check_db_exists, is_db_file


# Initialize module logger
_logger = Logger('local_db')
_logger.add_file_handler(format=ELF.FORMAT_LOGGER_NAME)



class DatabaseManager():
    '''
    Generic database manager wrapper class that allows for simple database operations to be performed on a local database file.
    '''
    def __init__(self, db_filename: str, database_obj_class, rel_db_dir: str='data\\db_files'):
        '''
        Initializes the DatabaseManager with a SQLAlchemy session and a database object class.

        Args:
            db_filename (str): The name of the database file (must be a valid .db filename).
        '''
        self.session = session
        self.


    def add_item(self, name, description=None):
        new_item = Item(name=name, description=description)
        self.session.add(new_item)
        self.session.commit()
        return new_item


    def fetch_all_items(self):
        return self.session.query(Item).all()


    def delete_item(self, item_id):
        item = self.session.query(Item).filter_by(id=item_id).first()
        if item:
            self.session.delete(item)
            self.session.commit()


    def update_item(self, item_id, name=None, description=None):
        item = self.session.query(Item).filter_by(id=item_id).first()
        if item:
            if name:
                item.name = name
            if description:
                item.description = description
            self.session.commit()
        return item


if __name__ == "__main__":
    pass