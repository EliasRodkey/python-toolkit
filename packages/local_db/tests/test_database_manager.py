#!python3
'''
tests.test_database_manager.py

This module contains tests for the DatabaseManager class from the local_db.database_manager module.

Classes:
    TestDatabaseManager:
        - Contains unit tests for various methods of the DatabaseManager class.

Functions:
    test_initialize_manager: Tests the initialization of the DatabaseManager class.
    test_add_item: Tests adding a single item to the database.
    test_add_item_multiple: Tests adding multiple items to the database.
    test_fetch_all_items: Tests fetching all items from the database.
    test_fetch_item_by_id: Tests fetching a single item by its ID.
    test_fetch_items_by_attribute: Tests fetching items based on a specific attribute.
    test_update_item: Tests updating an existing item in the database.
    test_delete_item: Tests deleting an item from the database.
'''

# Add current directory to path
import sys
sys.path.insert(0, '.')


# Third party imports
import pandas as pd
import pytest
import sqlalchemy
import time

# local imports
from local_db import DEFAULT_DB_DIRECTORY
from local_db.database_file import DatabaseFile
from local_db.database_manager import DatabaseManager
from .mock_table_object import MockTableObject
from .mock_table_object import TEST_ENTRY_1, TEST_ENTRY_2, TEST_ENTRY_3, INVALID_ENTRY, INVALID_DF


db_file = DatabaseFile('test.db')


@pytest.fixture(autouse=True)
def clean_database():
    '''Fixture to clean the database before and after each test'''
    db_manager = DatabaseManager(MockTableObject, db_file)

    try:
        # Setup: Clean the database
        db_manager.session.query(MockTableObject).delete()
        db_manager.session.commit()
        yield db_manager  # Provide the db_manager to the test
    except Exception:
        db_manager.session.rollback()  # Rollback the session if an exception occurs
        raise
    finally:
        # Teardown: Ensure the session is closed and the file is deleted
        db_manager.end_session()
        time.sleep(0.1)  # Add a short delay to release file locks
        db_manager.file.delete()


class TestDatabaseManager:
    '''Tests the DatabaseFile class from the local_db.database_file module'''

    # Functions
    def test_initialize_manager(self, clean_database):
        '''Tests the DatabaseManager class initialization'''

        # Check if the instance is created successfully
        assert isinstance(clean_database, DatabaseManager), 'DatabaseManager instance not created successfully.'
        assert isinstance(clean_database.file, DatabaseFile), 'DatabaseFile instance not created successfully.'

        # Check if the table class is set correctly
        assert clean_database.table_class == MockTableObject, 'Table class not set correctly.'

    
    def test_add_item(self, clean_database):
        '''Tests the add_item() method of the DatabaseManager class'''

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        assert clean_database.session.query(MockTableObject).count() == 1, 'Item not added to the database.'
        assert clean_database.session.query(MockTableObject).first().name == TEST_ENTRY_1['name'], 'Item name does not match.'
        assert clean_database.session.query(MockTableObject).first().age == TEST_ENTRY_1['age'], 'Item age does not match.'
        assert clean_database.session.query(MockTableObject).first().email == TEST_ENTRY_1['email'], 'Item email does not match.'


    def test_add_item_multiple(self, clean_database):
        '''Tests the add_item() method of the DatabaseManager class by adding multiple items'''

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        entry_1_name = clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_1['name']).first().name
        entry_1_age = clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_1['age']).first().age
        entry_2_name = clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_2['name']).first().name
        entry_2_age = clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_2['age']).first().age

        assert clean_database.session.query(MockTableObject).count() == 2, 'Multiple items not added to the database.'
        assert entry_1_name == TEST_ENTRY_1['name'], f'Item 1 name does not match {entry_1_name}.'
        assert entry_1_age == TEST_ENTRY_1['age'], f'Item 1 age does not match {entry_1_age}.'
        assert entry_2_name == TEST_ENTRY_2['name'], f'Item 2 name does not match {entry_2_name}.'
        assert entry_2_age == TEST_ENTRY_2['age'], f'Item 2 age does not match {entry_2_age}.'

    
    def test_add_item_invalid(self, clean_database):
        '''Tests the add_item() method of the DatabaseManager class with invalid data'''

        # Add an item with invalid data to the database
        with pytest.raises(TypeError):
            clean_database.add_item(**INVALID_ENTRY)

        assert clean_database.session.query(MockTableObject).count() == 0, 'Invalid item added to the database.'


    def test_add_item_duplicate(self, clean_database):
        '''
        Tests the add_item() method of the DatabaseManager class with duplicate data
        Deduplication logic is located in the table_class creation
        '''

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        with pytest.raises(sqlalchemy.exc.IntegrityError):
            clean_database.add_item(**TEST_ENTRY_1)

        assert clean_database.session.query(MockTableObject).count() == 1, 'Duplicate item added to the database.'


    # def test_append_dataframe(self):
    #     '''Tests the append_dataframe() method of the DatabaseManager class'''

    #     # Create a DatabaseManager instance
    #     db_manager = DatabaseManager(MockTableObject, db_file)

    #     # Create a DataFrame with test data
    #     df = pd.DataFrame([TEST_ENTRY_1, TEST_ENTRY_2])

    #     # Append the DataFrame to the database
    #     db_manager.append_dataframe(df)

    #     assert db_manager.session.query(MockTableObject).count() == 2, 'DataFrame not appended to the database.'


    def test_fetch_all_items(self, clean_database):
        '''Tests the fetch_all_items() method of the DatabaseManager class'''

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        entry_1_name = clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_1['name']).first().name
        entry_1_age = clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_1['age']).first().age
        entry_2_name = clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_2['name']).first().name
        entry_2_age = clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_2['age']).first().age

        query_result = clean_database.fetch_all_items()

        assert len(query_result) == 2, 'Not all items fetched from the database.'
        assert query_result[0].name == entry_1_name, f'Item 1 name does not match {query_result[0].name}.'
        assert query_result[0].age == entry_1_age, f'Item 1 age does not match {query_result[0].age}.'
        assert query_result[1].name == entry_2_name, f'Item 2 name does not match {query_result[1].name}.'
        assert query_result[1].age == entry_2_age, f'Item 2 age does not match {query_result[1].age}.'

    
    def test_fetch_item_by_id(self, clean_database):
        '''Tests the fetch_item_by_id() method of the DatabaseManager class'''

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        item = clean_database.fetch_item_by_id(2)

        assert clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_2['name']).first().name == item.name, 'Item not fetched by ID.'
        assert clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_2['age']).first().age == item.age, 'Item not fetched by ID.'
        assert clean_database.session.query(MockTableObject).filter_by(email=TEST_ENTRY_2['email']).first().email == item.email, 'Item not fetched by ID.'

    
    def test_fetch_items_by_attribute(self, clean_database):
        '''Tests the fetch_items_by_attribute() method of the DatabaseManager class'''

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        items = clean_database.fetch_items_by_attribute(age=TEST_ENTRY_3['age'])

        assert len(items) == 2, 'Items not fetched by attribute.'
        assert items[0].name == TEST_ENTRY_1['name'], f'Item 1 name does not match {items[0].name}.'
        assert items[0].age == TEST_ENTRY_1['age'], f'Item 1 age does not match {items[0].age}.'
        assert items[1].name == TEST_ENTRY_3['name'], f'Item 2 name does not match {items[1].name}.'
        assert items[1].age == TEST_ENTRY_3['age'], f'Item 2 age does not match {items[1].age}.'


    # def test_to_dataframe(self):
    #     '''Tests the to_dataframe() method of the DatabaseManager class'''

    #     # Create a DatabaseManager instance
    #     db_manager = DatabaseManager(MockTableObject, db_file)

    #     # Add multiple items to the database
    #     db_manager.add_item(**TEST_ENTRY_1)
    #     db_manager.add_item(**TEST_ENTRY_2)
    #     db_manager.add_item(**TEST_ENTRY_3)

    #     # Fetch all items from the database
    #     df = db_manager.to_dataframe()
    #     assert len(df) == 3, 'DataFrame does not contain the expected number of items.'
    #     assert df.iloc[0]['name'] == TEST_ENTRY_1['name'], f'Item 1 name does not match {df.iloc[0]["name"]}.'
    #     assert df.iloc[1]['name'] == TEST_ENTRY_2['name'], f'Item 2 name does not match {df.iloc[1]["name"]}.'
    #     assert df.iloc[2]['name'] == TEST_ENTRY_3['name'], f'Item 3 name does not match {df.iloc[2]["name"]}.'

    
    def test_update_item(self, clean_database):
        '''Tests the update_item() method of the DatabaseManager class'''

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        # Update the item in the database
        clean_database.update_item(1, **TEST_ENTRY_2)

        updated_item = clean_database.fetch_item_by_id(1)

        assert updated_item.name == 'Jane Doe', f'Item name not updated correctly: {updated_item.name}'
        assert updated_item.age == 25, f'Item age not updated correctly: {updated_item.age}'
    

    def test_delete_item(self, clean_database):
        '''Tests the delete_item() method of the DatabaseManager class'''

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        # Delete the item from the database
        clean_database.delete_item(1)

        assert clean_database.session.query(MockTableObject).count() == 0, 'Item not deleted from the database.'

    
    def test_df_columns_match_true(self, clean_database):
        '''Tests if the DataFrame columns match the database table columns'''

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        # Fetch all items from the database as a DataFrame
        df = clean_database.to_dataframe()

        # Check if the DataFrame columns match the database table columns
        assert clean_database._df_columns_match(df), 'DataFrame columns do not match database table columns.'


    def test_dict_columns_match_true(self, clean_database):
        '''Tests if the DataFrame columns match the database table columns'''

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        # Check if the DataFrame columns match the database table columns
        assert clean_database._dict_columns_match(TEST_ENTRY_2), 'DataFrame columns do not match database table columns.'

    
    def test_df_columns_match_false(self, clean_database):
        '''Tests if the DataFrame columns match the database table columns'''

        # Add an item with invalid data to the database
        with pytest.raises(TypeError):
            clean_database._df_types_match(INVALID_DF)

        # Check if the DataFrame columns match the database table columns
        assert clean_database.session.query(MockTableObject).count() == 0, 'DataFrame columns match database table columns.'


    def test_dict_columns_match_false(self, clean_database):
        '''Tests if the DataFrame columns match the database table columns'''

        # Add an item with invalid data to the database
        with pytest.raises(TypeError):
            clean_database._dict_types_match(INVALID_ENTRY)

        # Check if the DataFrame columns match the database table columns
        assert clean_database.session.query(MockTableObject).count() == 0, 'DataFrame columns match database table columns.'
