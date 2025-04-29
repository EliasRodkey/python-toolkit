#!python3
'''
tests.db_file_handler_test.py

this module contains tests for functions contained in the db__file_handler.py module

Funciton:
    create():
    - test_create_database: attempts to create a db file in a directory from a relative path

    DatabaseFile.move()
    - test_move_db_default: attempt to move a db file from a default location (cwd) to a default location (.\\data) 
    - test_move_db_custom_1: attempt to move a db file from a default location to a custom location (.\\data)
    - test_move_db_custom_2: attempt to move a db file from a custom location (cwd) to a default location (.\\data)
    - test_move_db_custom_3: attempt to move a db file from a custom location to a custom location (.\\data)
    - test_move_db_not_exist: attempt to move a db file that doesn't exist
    - test_move_db_target_exist: attempt to move a db file that already exists at target location

    delete_db()
    - test_delete_db_not_exist: attempts to delete a db file that does not exist
    - test_delete_db: attempts to delete a db file that does exist
    - test_delete_db_multiple: attempts to delete a db file that has multiple copies under one directory
'''

# Add current directory to path
import sys
sys.path.insert(0, '.')


# Standard library imports
import os
import random

# Third-Party library imports
import pytest

# local imports
from local_db import DEFAULT_DB_DIRECTORY
from local_db.database_file import DatabaseFile



# Constants
TEST_DB = 'test.db'
FAKE_DB = 'fake.db'


class TestDatabaseFile:
    # Functions
    def test_create_database_default(self):
        '''Tests the DatabaseFile.create() function from database_file by creating an new db file in the default db location and checking if it exists'''
        # Create db file in default location
        test_db = DatabaseFile(TEST_DB)
        test_db.create()
        assert os.path.exists(test_db.abspath)

        # Delete db file
        os.remove(os.path.abspath(os.path.join(DEFAULT_DB_DIRECTORY, TEST_DB)))
        assert not os.path.exists(test_db.abspath)


    def test_delete_database(self):
        '''Tests the DatabaseFile.delete() function from database_file by deleting a db file in the default db location'''
        # Create db file in default location
        test_db = DatabaseFile(TEST_DB)
        test_db.create()

        # Delete db file
        test_db.delete()
        assert not os.path.exists(test_db.abspath)


    def test_move_database_default(self):
        '''Tests the DatabaseFile.move() function from database_file by moving a db file from one location to another'''
        # Create db file in default location
        test_db = DatabaseFile(TEST_DB)
        test_db.create()

        # Move the database file to a new location
        new_db_dir = '.\\data'
        test_db.move(new_db_dir)
        assert test_db.directory == new_db_dir
        assert os.path.exists(test_db.abspath)

        # Delete db file
        test_db.delete()
        assert not os.path.exists(test_db.abspath)


    def test_move_database_custom_1(self):
        '''Tests the DatabaseFile.move() function from db_file_handler by moving a file from the cwd to the .\\data\\dbs dir'''
        # Create db file in the cwd location
        test_db = DatabaseFile(TEST_DB, directory=os.curdir)
        test_db.create()

        # Move db to the default db file location
        test_db.move(DEFAULT_DB_DIRECTORY)
        assert test_db.directory == DEFAULT_DB_DIRECTORY
        assert os.path.exists(test_db.abspath) 

        # Delete db file
        test_db.delete
        assert os.path.exists(test_db.abspath)


    def test_move_db_custom_2(self):
        '''Tests the DatabaseFile.move() function from db_file_handler by moving a file from the cwd to the a custom dir'''
        # Get a random directory from the project folder
        test_db = DatabaseFile(TEST_DB, directory=os.curdir)
        test_db.create()

        assert test_db.directory == os.curdir
        assert os.path.exists(test_db.abspath) 

        # Move db to a custom directory
        db_dir = 'data'
        test_db.move(db_dir)

        assert test_db.directory == db_dir
        assert os.path.exists(test_db.abspath) 

        # Delete db file
        test_db.delete()
        assert not os.path.exists(test_db.abspath)


    def test_move_db_target_exist(self):
        '''Tests the DatabaseFile.move() function from db_file_handler trying to move a db file to a dir where it already exists'''
        # Create a db file in cwd and in the .\data folder
        test_db = DatabaseFile(TEST_DB)
        test_db.create()

        # Capture original file information
        directory = test_db.directory
        file_path = test_db.file_path
        abspath = test_db.abspath

        # Try move db to the default db file location
        test_db.move(DEFAULT_DB_DIRECTORY)
        assert directory == test_db.directory
        assert file_path == test_db.file_path
        assert abspath == test_db.abspath
        assert os.path.exists(test_db.abspath)

        # Delete db files
        test_db.delete()
        assert not os.path.exists(test_db.abspath)


    def test_delete_db_not_exist(self):
        '''Tests the DatabaseFile.delete() function from db_file_handler by trying to delete a file that hasn't been created yet'''
        test_db = DatabaseFile(FAKE_DB)
        
        test_db.delete()
        assert not os.path.exists(test_db.abspath)