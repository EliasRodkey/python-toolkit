#!python3
'''
local_db_handler.utils.py

This module contains several helper functions for the local_db_handler package

Funcitons:
    - check_db_exists: checks a given database url / path to see if it has already been created
    - is_db_file: checks a string to see if it is a valid db filename
'''

# Standard library imports
import os
from enum import Enum

# Initiate module logger
from . import Logger, ELF, DEFAULT_DB_DIRECTORY


_logger = Logger('local_db_utils')
_logger.add_file_handler(format=ELF.FORMAT_LOGGER_NAME)


# Functions
def check_db_exists(db_filename:str, db_dir:str=DEFAULT_DB_DIRECTORY) -> bool:
    '''
    Checks a given db_url to see if it has already been created

    Args:
        db_filename: string of database file name
        db_dir: the directory where the file is expected to be found (default os.curdir)
    
    Returns:
        bool: True if the database file exists in the directory, False otherwise
    '''
    _logger.info(f'checking if {db_filename} exists in {db_dir}...')

    # Initialize return variables
    exists = False

    # Walk listed directory files
    for file in os.listdir(db_dir):
        _logger.debug(f'check_db_exists -> checking {db_filename} == {file}')

        # Check if file has the same name as db_filename
        if db_filename == file:
            exists = True

    return exists


def is_db_file(filename:str) -> bool:
    '''
    Takes a file name (full path or file title) and returns True if is .db
    
    Args:
        filename (str): the name of the file to check, must be a string
    
    Returns:
        bool: True if the file is a .db file, False otherwise
    '''
    try:
        # Check if filename is a string that ends with .db
        _logger.debug(f'is_db_file -> checking if {filename} is a .db file...')
        return filename.lower().endswith('.db')
    
    except AttributeError as e:
        # If filename is not a string, log the error and return False
        _logger.error(f'is_db_file -> {filename} is not a string: {e}')
        return False


if __name__ == "__main__":
    print(check_db_exists('test.db'))