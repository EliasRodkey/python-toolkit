#!python3
"""
tests.test_database_file.py

This module contains tests for the DatabaseFile class from the pleasant_database.database_file module.

Functions:
    DatabaseFile.create()
    - test_create_database_default: tests creating a database file in the default directory.

    DatabaseFile.delete()
    - test_delete_database: tests deleting an existing database file.
    - test_delete_db_not_exist: tests attempting to delete a database file that does not exist.

    DatabaseFile.move()
    - test_move_database_default: tests moving a database file to a new default directory.
    - test_move_database_custom_1: tests moving a database file from the current directory to the default directory.
    - test_move_db_custom_2: tests moving a database file from the current directory to a custom directory.
    - test_move_db_target_exist: tests attempting to move a database file to a directory where it already exists.
"""

# Add current directory to path
import sys
sys.path.insert(0, ".")

# Standard library imports
import os

# local imports
from pleasant_database import DEFAULT_DB_DIRECTORY
from pleasant_database.database_file import DatabaseFile


# Constants
TEST_DB = "test.db"
FAKE_DB = "fake.db"


class TestDatabaseFile:
    # Functions
    def test_create_database_default(self):
        """Tests the DatabaseFile.create() function from database_file by creating a new db file in the default db location and checking if it exists"""
        # Create db file in default location
        test_db = DatabaseFile(TEST_DB)
        test_db.create()
        assert os.path.exists(test_db.abspath)

        # Delete db file
        os.remove(os.path.abspath(os.path.join(DEFAULT_DB_DIRECTORY, TEST_DB)))
        assert not os.path.exists(test_db.abspath)


    def test_delete_database(self):
        """Tests the DatabaseFile.delete() function from database_file by deleting a db file in the default db location"""
        # Create db file in default location
        test_db = DatabaseFile(TEST_DB)
        test_db.create()

        # Delete db file
        test_db.delete()
        assert not os.path.exists(test_db.abspath)


    def test_move_database_default(self):
        """Tests the DatabaseFile.move() function from database_file by moving a db file from one location to another"""
        # Create db file in default location
        test_db = DatabaseFile(TEST_DB)
        test_db.create()

        # Move the database file to a new location
        new_db_dir = os.path.join(os.curdir, "data")
        test_db.move(new_db_dir)
        assert test_db.directory == new_db_dir
        assert os.path.exists(test_db.abspath)

        # Delete db file
        test_db.delete()
        assert not os.path.exists(test_db.abspath)


    def test_move_database_custom_1(self):
        """Tests the DatabaseFile.move() function from db_file_handler by moving a file from the cwd to the .\\data\\database dir"""
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
        """Tests the DatabaseFile.move() function from db_file_handler by moving a file from the cwd to the a custom dir"""
        # Get a random directory from the project folder
        test_db = DatabaseFile(TEST_DB, directory=os.curdir)
        test_db.create()

        assert test_db.directory == os.curdir
        assert os.path.exists(test_db.abspath) 

        # Move db to a custom directory
        db_dir = "data"
        test_db.move(db_dir)

        assert test_db.directory == db_dir
        assert os.path.exists(test_db.abspath) 

        # Delete db file
        test_db.delete()
        assert not os.path.exists(test_db.abspath)


    def test_move_db_target_exist(self):
        """Tests the DatabaseFile.move() function from db_file_handler trying to move a db file to a dir where it already exists"""
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
        """Tests the DatabaseFile.delete() function from db_file_handler by trying to delete a file that hasn"t been created yet"""
        test_db = DatabaseFile(FAKE_DB)

        test_db.delete()
        assert not os.path.exists(test_db.abspath)


    def test_init_invalid_name_raises(self):
        """Tests that DatabaseFile raises ValueError when given a non-.db filename"""
        import pytest
        with pytest.raises(ValueError):
            DatabaseFile("notadb.txt")


    def test_exists_true(self):
        """Tests that exists() returns True when the file has been created"""
        test_db = DatabaseFile(TEST_DB)
        test_db.create()
        assert test_db.exists() is True
        test_db.delete()


    def test_exists_false(self):
        """Tests that exists() returns False when the file has not been created"""
        test_db = DatabaseFile(FAKE_DB)
        assert test_db.exists() is False


    def test_create_idempotent(self):
        """Tests that calling create() twice does not raise and the file is still present"""
        test_db = DatabaseFile(TEST_DB)
        test_db.create()
        test_db.create()  # second call — should be a no-op
        assert os.path.exists(test_db.abspath)
        test_db.delete()


    def test_move_source_not_exist(self):
        """Tests that move() silently does nothing when the source file does not exist"""
        test_db = DatabaseFile("ghost.db")
        original_directory = test_db.directory
        original_abspath = test_db.abspath

        test_db.move("data")

        # Attributes must be unchanged — the file was never moved
        assert test_db.directory == original_directory
        assert test_db.abspath == original_abspath
        assert not os.path.exists(os.path.join("data", "ghost.db"))