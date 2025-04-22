#!python3
'''
local_db_handler.db_connections.py

This module contains functions which allow for connections to existing local database files

Funcitons:
    - create_engine_conn: creates a SQLalchemy engine object
    - create_session: creates and returns a SQLalchemy Session class object
'''

#Standard library imports
import logging

# Third-Party library imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger_db_connections = logging.getLogger(__name__)

# Functions
def create_engine_conn(rel_db_url:str):
    '''Create and returns an SQLalchemy engine from a given db URL string'''
    logger_db_connections.info(f'creating connection engine to {rel_db_url}...')

    return create_engine(f'sqlite:///{rel_db_url}')

def create_session(engine):
    '''Create and return a SQLalchemy session'''
    logger_db_connections.info(f'creating session for {engine}...')
    
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    pass