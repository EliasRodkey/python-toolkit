#!python3
'''
local_db_handler.utils.py

This module contains several helper functions for the local_db_handler package

Funcitons:
    - check_db_exists: checks a given database url / path to see if it has already been created
    - is_db_file: checks a string to see if it is a valid db filename
'''

# Standard library imports
import logging
import os

# Initiate module logger
logger_utils = logging.getLogger(__name__)


# Functions
def check_db_exists(db_filename:str, db_dir:str) -> bool:
    '''
    Checks a given db_url to see if it has already been created

    args:
        - db_filename: string of database file name
        - db_dir: the directory where the file is expected to be found (default os.curdir)
    '''
    logger_utils.info(f'checking if {db_filename} exists in {db_dir}...')

    # Initialize return variables
    exists = False

    # Walk listed directory files
    for file in os.listdir(db_dir):
        logger_utils.debug(f'checking {db_filename} == {file}')

        # Check if file has the same name as db_filename
        if db_filename == file:
            exists = True

    return exists


def is_db_file(filename:str) -> bool:
    '''takes a file name (full path or file title) and returns True if is .db'''
    try:
        logger_utils.debug(f'checking if {filename} is a .db file...')
        return filename.lower().endswith('.db')
    except AttributeError as e:
        logger_utils.error(f'{filename} is not a string: {e}')
        return False


if __name__ == "__main__":
    print(check_db_exists('test.db'))
    pass
