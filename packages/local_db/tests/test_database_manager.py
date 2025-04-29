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


# local imports
from local_db import DEFAULT_DB_DIRECTORY
from local_db.database_file import DatabaseFile
from local_db.database_manager import DatabaseManager
from .mock_table_object import MockTableObject, TEST_ENTRY_1, TEST_ENTRY_2, TEST_ENTRY_3


db_file = DatabaseFile('test.db')



class TestDatabaseManager:
    '''Tests the DatabaseFile class from the local_db.database_file module'''

    # Functions
    def test_initialize_manager(self):
        '''Tests the DatabaseManager class initialization'''
        # Create a DatabaseManager instance
        db_manager = DatabaseManager(MockTableObject, db_file)

        # Check if the instance is created successfully
        assert isinstance(db_manager, DatabaseManager), 'DatabaseManager instance not created successfully.'
        assert isinstance(db_manager.file, DatabaseFile), 'DatabaseFile instance not created successfully.'

        # Check if the table class is set correctly
        assert db_manager.table_class == MockTableObject, 'Table class not set correctly.'

        # Close the session and delete the database file
        db_manager.end_session()
        db_manager.file.delete()
        assert not db_manager.file.exists(), 'Database file should not exist after deletion.'

    
    def test_add_item(self):
        '''Tests the add_item() method of the DatabaseManager class'''

        # Create a DatabaseManager instance
        db_manager = DatabaseManager(MockTableObject, db_file)

        # Add an item to the database
        db_manager.add_item(**TEST_ENTRY_1)

        assert db_manager.session.query(MockTableObject).count() == 1, 'Item not added to the database.'
        assert db_manager.session.query(MockTableObject).first().name == TEST_ENTRY_1['name'], 'Item name does not match.'
        assert db_manager.session.query(MockTableObject).first().age == TEST_ENTRY_1['age'], 'Item age does not match.'
        assert db_manager.session.query(MockTableObject).first().email == TEST_ENTRY_1['email'], 'Item email does not match.'

        # Close the session and delete the database file
        db_manager.end_session()
        db_manager.file.delete()
        assert not db_manager.file.exists(), 'Database file should not exist after deletion.'


    def test_add_item_multiple(self):
        '''Tests the add_item() method of the DatabaseManager class by adding multiple items'''

        # Create a DatabaseManager instance
        db_manager = DatabaseManager(MockTableObject, db_file)

        # Add multiple items to the database
        db_manager.add_item(**TEST_ENTRY_1)
        db_manager.add_item(**TEST_ENTRY_2)

        entry_1_name = db_manager.session.query(MockTableObject).filter_by(name=TEST_ENTRY_1['name']).first().name
        entry_1_age = db_manager.session.query(MockTableObject).filter_by(age=TEST_ENTRY_1['age']).first().age
        entry_2_name = db_manager.session.query(MockTableObject).filter_by(name=TEST_ENTRY_2['name']).first().name
        entry_2_age = db_manager.session.query(MockTableObject).filter_by(age=TEST_ENTRY_2['age']).first().age

        assert db_manager.session.query(MockTableObject).count() == 2, 'Multiple items not added to the database.'
        assert entry_1_name == TEST_ENTRY_1['name'], f'Item 1 name does not match {entry_1_name}.'
        assert entry_1_age == TEST_ENTRY_1['age'], f'Item 1 age does not match {entry_1_age}.'
        assert entry_2_name == TEST_ENTRY_2['name'], f'Item 2 name does not match {entry_2_name}.'
        assert entry_2_age == TEST_ENTRY_2['age'], f'Item 2 age does not match {entry_2_age}.'

        # Close the session and delete the database file
        db_manager.end_session()
        db_manager.file.delete()
        assert not db_manager.file.exists(), 'Database file should not exist after deletion.'

    
    def test_fetch_all_items(self):
        '''Tests the fetch_all_items() method of the DatabaseManager class'''

        # Create a DatabaseManager instance
        db_manager = DatabaseManager(MockTableObject, db_file)

        # Add multiple items to the database
        db_manager.add_item(**TEST_ENTRY_1)
        db_manager.add_item(**TEST_ENTRY_2)

        entry_1_name = db_manager.session.query(MockTableObject).filter_by(name=TEST_ENTRY_1['name']).first().name
        entry_1_age = db_manager.session.query(MockTableObject).filter_by(age=TEST_ENTRY_1['age']).first().age
        entry_2_name = db_manager.session.query(MockTableObject).filter_by(name=TEST_ENTRY_2['name']).first().name
        entry_2_age = db_manager.session.query(MockTableObject).filter_by(age=TEST_ENTRY_2['age']).first().age

        query_result = db_manager.fetch_all_items()

        assert len(query_result) == 2, 'Not all items fetched from the database.'
        assert query_result[0].name == entry_1_name, f'Item 1 name does not match {query_result[0].name}.'
        assert query_result[0].age == entry_1_age, f'Item 1 age does not match {query_result[0].age}.'
        assert query_result[1].name == entry_2_name, f'Item 2 name does not match {query_result[1].name}.'
        assert query_result[1].age == entry_2_age, f'Item 2 age does not match {query_result[1].age}.'

        # Close the session and delete the database file
        db_manager.end_session()
        db_manager.file.delete()
        assert not db_manager.file.exists(), 'Database file should not exist after deletion.'

    
    def test_fetch_item_by_id(self):
        '''Tests the fetch_item_by_id() method of the DatabaseManager class'''

        # Create a DatabaseManager instance
        db_manager = DatabaseManager(MockTableObject, db_file)

        # Add multiple items to the database
        db_manager.add_item(**TEST_ENTRY_1)
        db_manager.add_item(**TEST_ENTRY_2)

        item = db_manager.fetch_item_by_id(2)

        assert db_manager.session.query(MockTableObject).filter_by(name=TEST_ENTRY_2['name']).first().name == item.name, 'Item not fetched by ID.'
        assert db_manager.session.query(MockTableObject).filter_by(age=TEST_ENTRY_2['age']).first().age == item.age, 'Item not fetched by ID.'
        assert db_manager.session.query(MockTableObject).filter_by(email=TEST_ENTRY_2['email']).first().email == item.email, 'Item not fetched by ID.'

        # Close the session and delete the database file
        db_manager.end_session()
        db_manager.file.delete()
        assert not db_manager.file.exists(), 'Database file should not exist after deletion.'

    
    def test_fetch_items_by_attribute(self):
        '''Tests the fetch_items_by_attribute() method of the DatabaseManager class'''

        # Create a DatabaseManager instance
        db_manager = DatabaseManager(MockTableObject, db_file)

        # Add multiple items to the database
        db_manager.add_item(**TEST_ENTRY_1)
        db_manager.add_item(**TEST_ENTRY_2)
        db_manager.add_item(**TEST_ENTRY_3)

        items = db_manager.fetch_items_by_attribute(age=TEST_ENTRY_3['age'])

        assert len(items) == 2, 'Items not fetched by attribute.'
        assert items[0].name == TEST_ENTRY_1['name'], f'Item 1 name does not match {items[0].name}.'
        assert items[0].age == TEST_ENTRY_1['age'], f'Item 1 age does not match {items[0].age}.'
        assert items[1].name == TEST_ENTRY_3['name'], f'Item 2 name does not match {items[1].name}.'
        assert items[1].age == TEST_ENTRY_3['age'], f'Item 2 age does not match {items[1].age}.'

        # Close the session and delete the database file
        db_manager.end_session()
        db_manager.file.delete()
        assert not db_manager.file.exists(), 'Database file should not exist after deletion.'

    
    def test_update_item(self):
        '''Tests the update_item() method of the DatabaseManager class'''

        # Create a DatabaseManager instance
        db_manager = DatabaseManager(MockTableObject, db_file)

        # Add an item to the database
        db_manager.add_item(**TEST_ENTRY_1)

        # Update the item in the database
        db_manager.update_item(1, **TEST_ENTRY_2)

        updated_item = db_manager.fetch_item_by_id(1)

        assert updated_item.name == 'Jane Doe', f'Item name not updated correctly: {updated_item.name}'
        assert updated_item.age == 25, f'Item age not updated correctly: {updated_item.age}'

        # Close the session and delete the database file
        db_manager.end_session()
        db_manager.file.delete()
        assert not db_manager.file.exists(), 'Database file should not exist after deletion.'
    

    def test_delete_item(self):
        '''Tests the delete_item() method of the DatabaseManager class'''

        # Create a DatabaseManager instance
        db_manager = DatabaseManager(MockTableObject, db_file)

        # Add an item to the database
        db_manager.add_item(**TEST_ENTRY_1)

        # Delete the item from the database
        db_manager.delete_item(1)

        assert db_manager.session.query(MockTableObject).count() == 0, 'Item not deleted from the database.'

        # Close the session and delete the database file
        db_manager.end_session()
        db_manager.file.delete()
        assert not db_manager.file.exists(), 'Database file should not exist after deletion.'