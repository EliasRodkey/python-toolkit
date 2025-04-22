#!python3
'''
local_db_handler.db_file_handler.py

this module creates, deletes, and archives database files within a python project

required project structure:

root\\
|───data
|   └──logs 
|───src
└   └──package

Class:
    - DBFile: a class which represents a db file object
        - create_db: creates a new database file in a given directory
        - delete_db: deletes a specified database file in a given directory
        - move_db: moves a specified database file from one directory to another inside of a project
'''
# Author: Elias Rodkey
# Created: 2024-17-11
# Version: 0.2.0
# License: MIT


# Standard library imports
import logging
import sqlite3
from dataclasses import dataclass, field

# Third-Party library imports
# import pandas as pd

# local imports
from .utils import os, check_db_exists


# Initialize module logger
logger_database_file = logging.getLogger(__name__)

# Constants
DEFAULT_DB_DIR = os.path.join(os.curdir, 'data')

@dataclass
class DatabaseFile():
    '''a dataclass which manages a single database file, name attribute must be valid .db filename'''
    name: str 
    directory: str
    path: str = field(init=False, repr=False)
    abspath: str = field(init=False, repr=False)

    def __post_init__(self):
        self.path = os.path.join(self.directory, self.name)
        self.abspath = os.path.abspath(self.path)

    def exists(self) -> bool:
        '''checks the if the database name exists in the given directiry''' 
        return check_db_exists(self.name, self.directory)
    
    def create(self):
        '''creates a new database file in a given directory, default .\\data. returns path(s) of file as a list'''
        logger_database_file.info(f'creating database file {self.name}...')
        if self.exists():
            logger_database_file.info(f'{self.name} already exists in {self.directory}')
        else:
            sqlite3.connect(self.path).close()
            logger_database_file.info(f'database file {self.name} created.')
            logger_database_file.debug(f'new db file path: {self.path}')

    def move(self, target_directory: str) -> None:
        '''moves a DatabaseFile object to a new directory'''
        logger_database_file.info(f'moving {self.name} from {self.directory} to {target_directory}...')

        # Check if db with that filename already exists in target dir. return False, not moved
        target_exists = check_db_exists(self.name, target_directory)
        if target_exists:
            # Does nothing if it already exists
            logger_database_file.error(f'{self.name} already exists in {target_directory}.')
        elif self.exists():
            # Moves to new directory if it doesn't exist and the current file exists
            new_path = os.path.join(target_directory, self.name)
            os.rename(self.path, new_path)
            self.path = new_path
            self.abspath = os.path.abspath(self.path)
            self.directory = target_directory
        else:
            logger_database_file.error(f'{self.name} cannot be moved because it doesn\'t exist in {self.directory}')
            

    def delete(self):
        '''deletes the file managed by the DatabaseFile instance'''
        os.remove(self.abspath)
        logger_database_file.info(f'{self.name} deleted from {self.directory}...')


if __name__ == "__main__":
    test_db = DatabaseFile('test.db', os.path.join(os.getcwd(), 'tests'))
    test_db.create()
    test_db.move(os.path.join(os.getcwd(), 'tests'))
    test_db.delete()