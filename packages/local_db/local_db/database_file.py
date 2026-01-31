#!python3
"""
local_db.database_file.py

this module creates, deletes, and archives database files within a python project

required project structure:

root\\
|───data
|   └──db_files
|   └──log_dir 
|───src
└   └──package

Class:
    - DatabaseFile: a class which represents a db file object
"""

# Standard library imports
import sqlite3

# Third-party imports
import os

# local imports
from . import DEFAULT_DB_DIRECTORY
from .utils import LoggingExtras, check_db_exists, is_db_file

# Initialize module logger
import logging
logger = logging.getLogger(__name__)



class DatabaseFile():
    """
    Class which manages a single database file, name attribute must be valid .db filename

    Functions:
        - exxists: checks if the database file exists in the given directory
        - create: creates a new database file in the given directory
        - move: moves the database file to a new directory
        - delete: deletes the database file from the filesystem
    """
    def __init__(self, name, directory=DEFAULT_DB_DIRECTORY):
        """
        initializes a DatabaseFile object with a name and directory

        Args:
            name (str): the name of the database file, must be a valid .db filename
            directory (str): the relative directory where the database file is located, default is "os.curdir/data/db_files"
        """
        # Check if the name is a valid database filename
        if is_db_file(name):
            self.name = name
        else:
            logger.error(f"{name} is not a valid database filename.", extra={LoggingExtras.FILE_NAME: name})
            raise ValueError(f"Database file {name} is not a valid database filename.")
        
        # Initialize the directory and path attributes
        self.directory = directory
        self.file_path = os.path.join(self.directory, self.name)
        self.abspath = os.path.abspath(self.file_path)

        # If the directory does not exist, create it
        if not os.path.exists(self.directory):
            logger.warning(f"Database directory {directory} does not exist. Creating directory...", extra={LoggingExtras.FILE_PATH: directory})
            os.makedirs(directory)


    def exists(self) -> bool:
        """checks the if the database name exists in the given directiry""" 
        return check_db_exists(self.name, self.directory)
    

    def create(self):
        """creates a new database file in a given directory, default .\\data."""
        logger.info(f"Creating database file {self.name}...")
        if self.exists():
            logger.info(f"Database file {self.name} already exists in {self.directory}", extra={LoggingExtras.FILE_PATH: os.path.join(self.directory, self.name)})
        else:
            sqlite3.connect(self.file_path).close()
            logger.info(f"Database file {self.name} created.", extra={LoggingExtras.FILE_NAME: self.name})
            logger.debug(f"New db file path: {self.file_path}", extra={LoggingExtras.FILE_PATH: self.file_path})


    def move(self, target_directory: str) -> None:
        """moves a DatabaseFile object to a new directory"""
        logger.info(f"Moving {self.name} from {self.directory} to {target_directory}...", extra={
                                                                                        LoggingExtras.FILE_NAME: self.name, 
                                                                                        LoggingExtras.FILE_PATH: target_directory
                                                                                        })

        # Check if db with that filename already exists in target dir. return False, not moved
        target_exists = check_db_exists(self.name, target_directory)
        if target_exists:
            # Does nothing if it already exists
            logger.error(f"Database file {self.name} already exists in {target_directory}.", extra={
                                                                                        LoggingExtras.FILE_NAME: self.name, 
                                                                                        LoggingExtras.FILE_PATH: target_directory
                                                                                        })
        elif self.exists():
            # Moves to new directory if it doesn"t exist and the current file exists
            new_path = os.path.join(target_directory, self.name)
            os.rename(self.file_path, new_path)
            self.file_path = new_path
            self.abspath = os.path.abspath(self.file_path)
            self.directory = target_directory
        else:
            logger.error(f"Database file {self.name} cannot be moved because it doesn't exist in {self.directory}", extra={
                                                                                        LoggingExtras.FILE_NAME: self.name, 
                                                                                        LoggingExtras.FILE_PATH: self.directory
                                                                                        })
            

    def delete(self):
        """deletes the file managed by the DatabaseFile instance"""
        if os.path.exists(self.abspath):
            os.remove(self.abspath)
            logger.info(f"Database file {self.name} deleted from {self.directory}...", extra={
                                                                                        LoggingExtras.FILE_NAME: self.name, 
                                                                                        LoggingExtras.FILE_PATH: self.directory
                                                                                        })
        else:
            logger.error(f"DatabaseFile.delete() -> {self.name} does not exist in {self.directory}. Cannot delete.", extra={
                                                                                                                    LoggingExtras.FILE_NAME: self.name, 
                                                                                                                    LoggingExtras.FILE_PATH: self.directory
                                                                                                                    })
