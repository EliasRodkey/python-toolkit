#!python3
'''
local_db_handler.local_db.py

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

# Standard library imports
import logging

# Third-Party library imports
# import pandas as pd

# local imports
from .db_connections import create_engine_conn, create_session
from .database_file import create_db, move_db, delete_db
from .utils import check_db_exists, is_db_file


# Initialize module logger
logger_local_db = logging.getLogger(__name__)


class LocalDB():
    '''
    Database connection object
    '''
    def __init__(self):
        pass

if __name__ == "__main__":
    pass