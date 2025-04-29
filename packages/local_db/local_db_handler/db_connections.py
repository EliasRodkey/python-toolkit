#!python3
'''
local_db_handler.db_connections.py

This module contains functions which allow for connections to existing local database files

Funcitons:
    - create_engine_conn: creates a SQLalchemy engine object
    - create_session: creates and returns a SQLalchemy Session class object
'''

# Initiate module logger
from . import Logger, ELF
from .utils import DatabaseDefaults

# Third-Party library imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


_logger = Logger('local_db_connections')
_logger.add_file_handler(format=ELF.FORMAT_LOGGER_NAME)



# Functions
def create_engine_conn(relative_db_path:str=DatabaseDefaults.RELATIVE_PATH) -> object:
    '''
    Create and returns an SQLalchemy engine from a given db URL string

    Args:
        relative_db_path (str): the relative path to the database file, must be a valid .db filename
    
    Returns:
        engine: a SQLalchemy engine object which can be used to connect to the database
    '''

    _logger.info(f'creating connection engine to {relative_db_path}...')

    return create_engine(f'sqlite:///{relative_db_path}')


def create_session(engine):
    '''
    Create and return a SQLalchemy session
    
    Args:
        engine: a SQLalchemy engine object which can be used to connect to the database
    
    Returns:
        Session: a SQLalchemy session object which can be used to interact with the database
    '''
    _logger.info(f'creating session for {engine}...')
    
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    pass