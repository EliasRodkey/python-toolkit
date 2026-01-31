#!python3
"""
local_db.database_connections.py

This module contains functions which allow for connections to existing local database files

Functions:
    - create_engine_conn: creates a SQLalchemy engine object
    - create_session: creates and returns a SQLalchemy Session class object
"""

# Third-Party library imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Local Imports
from local_db import DEFAULT_DB_DIRECTORY
from local_db.utils import LoggingExtras

# Initialize module logger
import logging
logger = logging.getLogger(__name__)


# Functions
def create_engine_conn(relative_db_path:str=DEFAULT_DB_DIRECTORY) -> object:
    """
    Create and returns an SQLalchemy engine from a given db URL string

    Args:
        relative_db_path (str): the relative path to the database file, must be a valid .db filename
    
    Returns:
        engine: a SQLalchemy engine object which can be used to connect to the database
    """

    logger.info(f"Creating connection engine to {relative_db_path}...", extra={
                                                                        LoggingExtras.FILE_PATH: relative_db_path
                                                                    })

    return create_engine(f"sqlite:///{relative_db_path}")


def create_session(engine):
    """
    Create and return a SQLalchemy session
    
    Args:
        engine: a SQLalchemy engine object which can be used to connect to the database
    
    Returns:
        Session: a SQLalchemy session object which can be used to interact with the database
    """
    logger.info(f"Creating session for {engine}...")
    
    Session = sessionmaker(bind=engine)
    return Session()