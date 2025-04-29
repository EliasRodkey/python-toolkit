#!python3
'''
tests.db_file_handler_test.py

this module contains tests for functions contained in the db__file_handler.py module

Funciton:
    create():
    - test_create_database: attempts to create a db file in a directory from a relative path

    move_db()
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
from local_db_handler.database_file import DatabaseFile


# Constants
TEST_DB = 'test.db'
FAKE_DB = 'fake.db'
TEST_DB_DIR = os.path.join(os.curdir, 'data')
TEST_DB_PATH = os.path.join(TEST_DB_DIR, TEST_DB)
TEST_DB_ABS_DIR = os.path.abspath(TEST_DB_DIR)
TEST_DB_ABS_PATH = os.path.abspath(TEST_DB_PATH)



# Functions
def test_create_database():
    '''Tests the DatabaseFile.create() function from database_file by creating an new db file in the default db location and checking if it exists'''
    # Create db file in default location
    test_db = DatabaseFile(TEST_DB)
    test_db.create()
    assert os.path.exists(test_db.abspath)

    # Delete db file
    os.remove(os.path.join(TEST_DB_ABS_PATH))
    assert not os.path.exists(test_db.abspath)


# Pytest parameters for move db file test
@pytest.mark.parametrize(('db_dir_1', 'db_dir_2'), [
    (get_two_distinct_dir()),
    (get_two_distinct_dir()),
    (get_two_distinct_dir()),
])

def test_move_database(db_dir_1:str, db_dir_2:str):
    '''Tests the DatabaseFile.move() function from database_file by moving a db file from one location to another'''
    # Create db file in default location
    test_db = DatabaseFile(TEST_DB, db_dir_1)
    test_db.create()

    # Move the database file to a new location
    test_db.move(db_dir_2)
    assert test_db.directory == db_dir_2
    assert os.path.exists(test_db.abspath)

    # Delete db file
    os.remove(os.path.join(db_dir_2, TEST_DB))
    assert not os.path.exists(test_db.abspath)


# def test_move_db_default():
#     '''Tests the move_db() function from db_file_handler by moving a file from the cwd to the .\\data dir'''
#     # Create db file in the cwd location
#     create_db(TEST_DB, db_dir=os.curdir)

#     # Move db to the default db file location
#     moved = move_db(TEST_DB)
#     assert moved

#     # Delete db file
#     deleted = delete_db(TEST_DB)
#     assert deleted[0] == DEFAULT_TEST_DB_PATH


# def test_move_db_custom_1():
#     '''Tests the move_db() function from db_file_handler by moving a file from the cwd to the a custom dir'''
#     # Get a random directory from the project folder
#     rand_target_dir = get_random_dir()

#     # Create a db file in the cwd
#     create_db(TEST_DB, db_dir=os.curdir)

#     # Move db file to the rand dir
#     moved = move_db(TEST_DB, target_db_dir=rand_target_dir)
#     assert moved

#     # Delete db file
#     deleted = delete_db(TEST_DB, db_dir=rand_target_dir)
#     assert deleted[0] == os.path.join(rand_target_dir, TEST_DB)


# def test_move_db_custom_2():
#     '''Tests the move_db() function from db_file_handler by moving a file from a custom dir to the .\\data dir'''
#     # Get a random directory from the project folder
#     rand_src_dir = get_random_dir()

#     # Create a db file in the random dir
#     create_db(TEST_DB, db_dir=rand_src_dir)

#     # Move the db file to the default dir
#     moved = move_db(TEST_DB, db_dir=rand_src_dir)
#     assert moved

#     # Delete db file
#     deleted = delete_db(TEST_DB)
#     assert deleted[0] == DEFAULT_TEST_DB_PATH


# def test_move_db_custom_3():
#     '''Tests the move_db() function from db_file_handler by moving a file from a custom dir to a custom dir'''
#     # Get a random source and target directory from the project folder
#     cwd = os.getcwd()
#     directories = [d for d in os.listdir() if os.path.isdir(os.path.join(cwd, d))]
#     rand_src_dir = random.choice(directories)
#     rand_target_dir = random.choice(directories)
#     while rand_src_dir == rand_target_dir:
#         rand_src_dir = random.choice(directories)
#         rand_target_dir = random.choice(directories)

#     # Create a db file in the random source dir
#     create_db(TEST_DB, db_dir=rand_src_dir)

#     # Move db file from random source db to random target db
#     moved = move_db(TEST_DB, db_dir=rand_src_dir, target_db_dir=rand_target_dir)
#     assert moved

#     # Delete db file
#     deleted = delete_db(TEST_DB, db_dir=rand_target_dir)
#     assert deleted[0] == os.path.join(rand_target_dir, TEST_DB)


# def test_move_db_not_exist():
#     '''Tests the move_db() function from db_file_handler trying to move a db file that doesn't exist'''
#     # Try move db to the default db file location
#     moved = move_db(FAKE_DB)
#     assert not moved


# def test_move_db_target_exist():
#     '''Tests the move_db() function from db_file_handler trying to move a db file to a dir where it already exists'''
#     # Create a db file in cwd and in the .\data folder
#     create_db(TEST_DB)
#     create_db(TEST_DB, db_dir=CUSTOM_TEST_DB_DIR)

#     # Try move db to the default db file location
#     moved = move_db(TEST_DB, db_dir=CUSTOM_TEST_DB_DIR)
#     assert not moved

#     # Delete db files
#     deleted = delete_db(TEST_DB, delete_multiple=True)
#     assert deleted == [DEFAULT_TEST_DB_PATH, CUSTOM_TEST_DB_PATH]


# def test_delete_db_not_exist():
#     '''Tests the delete_db() function from db_file_handler by trying to delete a file that doesn't exist'''
#     deleted = delete_db(FAKE_DB)
#     assert len(deleted) == 0


# def test_delete_db():
#     '''Tests the delete_db() function from db_file_handler by trying to delete a file that doesn't exist'''
#     create_db(TEST_DB)
#     deleted = delete_db(TEST_DB)
#     assert deleted[0] == DEFAULT_TEST_DB_PATH


# def test_delete_db_multiple():
#     '''Tests the delete_db() function from db_file_handler by trying to delete a file that doesn't exist'''
#     create_db(TEST_DB)
#     create_db(TEST_DB, db_dir=CUSTOM_TEST_DB_DIR)
#     deleted = delete_db(TEST_DB, delete_multiple=True)
#     assert deleted == [DEFAULT_TEST_DB_PATH, CUSTOM_TEST_DB_PATH]