#!python3
"""
local_db.utils.py

This module contains several helper functions for the local_db_handler package

Funcitons:
    - check_db_exists: checks a given database url / path to see if it has already been created
    - is_db_file: checks a string to see if it is a valid db filename
"""

# Standard library imports
import os
import pandas as pd
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, LargeBinary, create_engine
from sqlalchemy.inspection import inspect

# Import logging dependencies
import logging
from loggers import configure_logger, LoggingHandlerController

# Local imports
from . import DEFAULT_DB_DIRECTORY

# Initiate module logger
logger = logging.getLogger(__name__)
log_handler_controller: LoggingHandlerController = configure_logger(logger)


# Functions
def check_db_exists(db_filename:str, db_dir:str=DEFAULT_DB_DIRECTORY) -> bool:
    """
    Checks a given db_url to see if it has already been created

    Args:
        db_filename: string of database file name
        db_dir: the directory where the file is expected to be found (default os.curdir)
    
    Returns:
        bool: True if the database file exists in the directory, False otherwise
    """
    logger.info(f"checking if {db_filename} exists in {db_dir}...")

    # Initialize return variables
    exists = False

    # Walk listed directory files
    for file in os.listdir(db_dir):
        logger.debug(f"check_db_exists -> checking {db_filename} == {file}")

        # Check if file has the same name as db_filename
        if db_filename == file:
            exists = True

    return exists


def is_db_file(filename:str) -> bool:
    """
    Takes a file name (full path or file title) and returns True if is .db
    
    Args:
        filename (str): the name of the file to check, must be a string
    
    Returns:
        bool: True if the file is a .db file, False otherwise
    """
    try:
        # Check if filename is a string that ends with .db
        logger.debug(f"is_db_file -> checking if {filename} is a .db file...")
        return filename.lower().endswith(".db")
    
    except AttributeError as e:
        # If filename is not a string, log the error and return False
        logger.error(f"is_db_file -> {filename} is not a string: {e}")
        return False


def map_dtype_to_sql(dtype):
    """
    Maps a given numpy data type to its corresponding SQLAlchemy type.

    Args:
        dtype: The numpy data type to be mapped.
    
    Returns:
        The corresponding SQLAlchemy type as a string.
    """
    if pd.api.types.is_integer_dtype(dtype):
        return Integer
    
    elif pd.api.types.is_float_dtype(dtype):
        return Float
    
    elif pd.api.types.is_bool_dtype(dtype):
        return Boolean
    
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return DateTime
    
    elif pd.api.types.is_object_dtype(dtype):
        return String
    
    elif pd.api.types.is_string_dtype(dtype):
        return String
    
    elif pd.api.types.is_binary_dtype(dtype):  # Check for binary data
        return LargeBinary
    
    elif pd.api.types.is_list_dtype(dtype):
        return LargeBinary  # or String, depending on your use case
    
    elif pd.api.types.is_dict_dtype(dtype):
        return LargeBinary  # or String, depending on your use case
    
    else:
        raise ValueError(f"Unsupported pandas dtype: {dtype}")
    

def map_dtype_list_to_sql(dtype_list):
    """
    Maps a list of numpy data types to their corresponding SQLAlchemy types.

    Args:
        dtype_list: A list of numpy data types to be mapped.
    
    Returns:
        A list of corresponding SQLAlchemy types as strings.
    """
    return [map_dtype_to_sql(dtype) for dtype in dtype_list]


def orm_list_to_dataframe(rows):
    """
    Returns a pandas DataFrame from a list of ORM objects

    Args:
        rows: list of ORM objects (SQLAlchemy model instances, Base subclasses)

    Returns:
        pd.DataFrame: DataFrame containing the data from the ORM objects
    """
    return pd.DataFrame([
        {attr.key: getattr(row, attr.key)
         for attr in inspect(row).mapper.column_attrs}
        for row in rows
    ])


if __name__ == "__main__":
    print(check_db_exists("test.db"))

    print(map_dtype_list_to_sql([int, str, float]))