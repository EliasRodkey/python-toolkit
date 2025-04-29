#!python3
'''
local_db_handler.db_file_handler.py

this module creates, deletes, and archives database files within a python project

required project structure:

root\\
|───data
|   └──db_files
|   └──log_dir 
|───src
└   └──package

Class:
    - DBFile: a class which represents a db file object
        - create_db: creates a new database file in a given directory
        - delete_db: deletes a specified database file in a given directory
        - move_db: moves a specified database file from one directory to another inside of a project
'''

# Standard library imports
import sqlite3

# local imports
from . import Logger, ELF, DEFAULT_DB_DIRECTORY
from .utils import os, check_db_exists, is_db_file

# Initialize module logger
_logger = Logger('local_db_file')
_logger.add_file_handler(format=ELF.FORMAT_LOGGER_NAME)



class DatabaseFile():
    '''a dataclass which manages a single database file, name attribute must be valid .db filename'''
    def __init__(self, name, directory=DEFAULT_DB_DIRECTORY):
        '''
        initializes a DatabaseFile object with a name and directory

        Args:
            name (str): the name of the database file, must be a valid .db filename
            directory (str): the relative directory where the database file is located, default is 'os.curdir/data/db_files'
        '''
        # Check if the name is a valid database filename
        if is_db_file(name):
            self.name = name
        else:
            _logger.error(f'DatabaseFile.__init__() -> {name} is not a valid database filename.')
            raise ValueError(f'{name} is not a valid database filename.')
        
        # Initialize the directory and path attributes
        self.directory = directory
        self.file_path = os.path.join(self.directory, self.name)
        self.abspath = os.path.abspath(self.file_path)

        # If the directory does not exist, create it
        if not os.path.exists(self.directory):
            _logger.warning(f'DatabaseFile.__init__() -> {directory} does not exist. Creating at {self.file_path}...')
            os.makedirs(directory)


    def exists(self) -> bool:
        '''checks the if the database name exists in the given directiry''' 
        return check_db_exists(self.name, self.directory)
    

    def create(self):
        '''creates a new database file in a given directory, default .\\data.'''
        _logger.info(f'creating database file {self.name}...')
        if self.exists():
            _logger.info(f'{self.name} already exists in {self.directory}')
        else:
            sqlite3.connect(self.file_path).close()
            _logger.info(f'database file {self.name} created.')
            _logger.debug(f'DatabaseFile.create() -> new db file path: {self.file_path}')


    def move(self, target_directory: str) -> None:
        '''moves a DatabaseFile object to a new directory'''
        _logger.info(f'moving {self.name} from {self.directory} to {target_directory}...')

        # Check if db with that filename already exists in target dir. return False, not moved
        target_exists = check_db_exists(self.name, target_directory)
        if target_exists:
            # Does nothing if it already exists
            _logger.error(f'DatabaseFile.move() -> {self.name} already exists in {target_directory}.')
        elif self.exists():
            # Moves to new directory if it doesn't exist and the current file exists
            new_path = os.path.join(target_directory, self.name)
            os.rename(self.file_path, new_path)
            self.file_path = new_path
            self.abspath = os.path.abspath(self.file_path)
            self.directory = target_directory
        else:
            _logger.error(f'DatabaseFile.move() -> {self.name} cannot be moved because it doesn\'t exist in {self.directory}')
            

    def delete(self):
        '''deletes the file managed by the DatabaseFile instance'''
        if os.path.exists(self.abspath):
            os.remove(self.abspath)
            _logger.info(f'{self.name} deleted from {self.directory}...')
        else:
            _logger.error(f'DatabaseFile.delete() -> {self.name} does not exist in {self.directory}. Cannot delete.')


if __name__ == "__main__":
    test_db = DatabaseFile('test.db', os.path.join(os.getcwd(), 'tests'))
    test_db.create()
    test_db.move(os.path.join(os.getcwd(), 'tests'))
    test_db.delete()