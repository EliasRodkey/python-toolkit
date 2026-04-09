#!python3
"""
tests.test_database_manager.py

This module contains tests for the DatabaseManager class from the pleasant_database.database_manager module.

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
"""

# Add current directory to path
import sys
sys.path.insert(0, ".")


# Third party imports
import pandas as pd
import pytest
import time

# local imports
from pleasant_database import DEFAULT_DB_DIRECTORY
from pleasant_database.base_table import DatabaseIntegrityError, ItemNotFoundError
from pleasant_database.database_file import DatabaseFile
from pleasant_database.database_manager import DatabaseManager
from .mock_table_object import MockTableObject, DatetimeMockTableObject
from .mock_table_object import TEST_ENTRY_1, TEST_ENTRY_2, TEST_ENTRY_3, INVALID_ENTRY, INVALID_DF
from .mock_table_object import DATE_ENTRY_1, DATE_ENTRY_2, DATE_ENTRY_3, SWITCHED_DATE_ENTRY


db_file = DatabaseFile("test.db")


@pytest.fixture(autouse=True)
def clean_database():
    """Fixture to clean the database before and after each test"""
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
    """Tests the DatabaseFile class from the pleasant_database.database_file module"""

    # Functions
    def test_initialize_manager(self, clean_database):
        """Tests the DatabaseManager class initialization"""

        # Check if the instance is created successfully
        assert isinstance(clean_database, DatabaseManager), "DatabaseManager instance not created successfully."
        assert isinstance(clean_database.file, DatabaseFile), "DatabaseFile instance not created successfully."

        # Check if the table class is set correctly
        assert clean_database.table_class == MockTableObject, "Table class not set correctly."

    
    def test_add_item(self, clean_database):
        """Tests the add_item() method of the DatabaseManager class"""

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        assert clean_database.session.query(MockTableObject).count() == 1, "Item not added to the database."
        assert clean_database.session.query(MockTableObject).first().name == TEST_ENTRY_1["name"], "Item name does not match."
        assert clean_database.session.query(MockTableObject).first().age == TEST_ENTRY_1["age"], "Item age does not match."
        assert clean_database.session.query(MockTableObject).first().email == TEST_ENTRY_1["email"], "Item email does not match."


    def test_add_item_multiple(self, clean_database):
        """Tests the add_item() method of the DatabaseManager class by adding multiple items"""

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        entry_1_name = clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_1["name"]).first().name
        entry_1_age = clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_1["age"]).first().age
        entry_2_name = clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_2["name"]).first().name
        entry_2_age = clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_2["age"]).first().age

        assert clean_database.session.query(MockTableObject).count() == 2, "Multiple items not added to the database."
        assert entry_1_name == TEST_ENTRY_1["name"], f"Item 1 name does not match {entry_1_name}."
        assert entry_1_age == TEST_ENTRY_1["age"], f"Item 1 age does not match {entry_1_age}."
        assert entry_2_name == TEST_ENTRY_2["name"], f"Item 2 name does not match {entry_2_name}."
        assert entry_2_age == TEST_ENTRY_2["age"], f"Item 2 age does not match {entry_2_age}."

    
    def test_add_item_invalid(self, clean_database):
        """Tests the add_item() method of the DatabaseManager class with invalid data"""

        # Add an item with invalid data to the database
        with pytest.raises(TypeError):
            clean_database.add_item(**INVALID_ENTRY)

        assert clean_database.session.query(MockTableObject).count() == 0, "Invalid item added to the database."


    def test_add_item_duplicate(self, clean_database):
        """
        Tests the add_item() method of the DatabaseManager class with duplicate data
        Deduplication logic is located in the table_class creation
        """

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        with pytest.raises(DatabaseIntegrityError) as exc_info:
            clean_database.add_item(**TEST_ENTRY_1)

        assert exc_info.value.column == "email"
        assert clean_database.session.query(MockTableObject).count() == 1, "Duplicate item added to the database."


    def test_append_dataframe(self, clean_database):
        """Tests the append_dataframe() method of the DatabaseManager class"""

        # Create a DataFrame with test data
        df = pd.DataFrame([TEST_ENTRY_1, TEST_ENTRY_2])

        # Append the DataFrame to the database
        clean_database.append_dataframe(df)

        assert clean_database.session.query(MockTableObject).count() == 2, "DataFrame not appended to the database."


    def test_fetch_all_items(self, clean_database):
        """Tests the fetch_all_items() method of the DatabaseManager class"""

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        entry_1_name = clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_1["name"]).first().name
        entry_1_age = clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_1["age"]).first().age
        entry_2_name = clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_2["name"]).first().name
        entry_2_age = clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_2["age"]).first().age

        query_result = clean_database.fetch_all_items()

        assert len(query_result) == 2, "Not all items fetched from the database."
        assert query_result[0].name == entry_1_name, f"Item 1 name does not match {query_result[0].name}."
        assert query_result[0].age == entry_1_age, f"Item 1 age does not match {query_result[0].age}."
        assert query_result[1].name == entry_2_name, f"Item 2 name does not match {query_result[1].name}."
        assert query_result[1].age == entry_2_age, f"Item 2 age does not match {query_result[1].age}."

    
    def test_fetch_item_by_id(self, clean_database):
        """Tests the fetch_item_by_id() method of the DatabaseManager class"""

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        item = clean_database.fetch_item_by_id(2)

        assert clean_database.session.query(MockTableObject).filter_by(name=TEST_ENTRY_2["name"]).first().name == item.name, "Item not fetched by ID."
        assert clean_database.session.query(MockTableObject).filter_by(age=TEST_ENTRY_2["age"]).first().age == item.age, "Item not fetched by ID."
        assert clean_database.session.query(MockTableObject).filter_by(email=TEST_ENTRY_2["email"]).first().email == item.email, "Item not fetched by ID."

    
    def test_fetch_items_by_attribute(self, clean_database):
        """Tests the fetch_items_by_attribute() method of the DatabaseManager class"""

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        items = clean_database.fetch_items_by_attribute(age=TEST_ENTRY_3["age"])

        assert len(items) == 2, "Items not fetched by attribute."
        assert items[0].name == TEST_ENTRY_1["name"], f"Item 1 name does not match {items[0].name}."
        assert items[0].age == TEST_ENTRY_1["age"], f"Item 1 age does not match {items[0].age}."
        assert items[1].name == TEST_ENTRY_3["name"], f"Item 2 name does not match {items[1].name}."
        assert items[1].age == TEST_ENTRY_3["age"], f"Item 2 age does not match {items[1].age}."

    
    def test_filter_items_single_filter(self, clean_database):
        """Tests the filter_items() method of the DatabaseManager class with a single filter"""
        # Arrange
        clean_database.add_item(name="coffee", age=4, email="food")
        clean_database.add_item(name="book", age=12, email="education")

        # Act
        results = clean_database.filter_items({"email": "food"})

        # Assert
        assert len(results) == 1
        assert results[0].name == "coffee"
        assert results[0].age == 4


    def test_filter_items_multiple_filters(self, clean_database):
        """Tests the filter_items() method of the DatabaseManager class with multiple filters"""
        # Arrange
        clean_database.add_item(name="book", age=3, email="transportation")
        clean_database.add_item(name="sandwich", age=8, email="food")
        clean_database.add_item(name="book", age=10, email="education")

        # Act
        results = clean_database.filter_items({
            "name": "book",
            "age": (">", 5)
        })

        # Assert
        assert len(results) == 1
        assert results[0].email == "education"


    def test_filter_items_no_matches(self, clean_database):
        """Tests the filter_items() method of the DatabaseManager class with no matching results"""
        # Arrange
        clean_database.add_item(name="coffee", age=3, email="food")

        # Act
        results = clean_database.filter_items({"email": "transport"})

        # Assert
        assert results == []


    def test_filter_items_invalid_column_raises(self, clean_database):
        """Tests the filter_items() method of the DatabaseManager class with invalid column name"""
        with pytest.raises(AttributeError):
            clean_database.filter_items({"nonexistent_column": "value"})


    def test_filter_items_invalid_operator_raises(self, clean_database):
        """Tests the filter_items() method of the DatabaseManager class with unsupported operator"""
        clean_database.add_item(name="coffee", age=3, email="food")

        with pytest.raises(ValueError):
            clean_database.filter_items({"age": ("~=", 5)})


    def test_filter_items_list_of_tuples_range(self, clean_database):
        """Tests filter_items() with a list of tuples to apply multiple constraints on one column"""
        # Arrange
        clean_database.add_item(name="low", age=3, email="a")
        clean_database.add_item(name="mid", age=10, email="b")
        clean_database.add_item(name="high", age=20, email="c")

        # Act — age between 6 and 15 inclusive
        results = clean_database.filter_items({"age": [(">=", 6), ("<=", 15)]})

        # Assert
        assert len(results) == 1
        assert results[0].name == "mid"


    def test_filter_items_list_of_tuples_mixed_columns(self, clean_database):
        """Tests filter_items() combining a list-of-tuples column constraint with a single-spec constraint"""
        # Arrange
        clean_database.add_item(name="alpha", age=5, email="x")
        clean_database.add_item(name="alpha", age=15, email="y")
        clean_database.add_item(name="beta", age=10, email="z")

        # Act — name == "alpha" AND age between 8 and 20
        results = clean_database.filter_items({"name": "alpha", "age": [(">=", 8), ("<=", 20)]})

        # Assert
        assert len(results) == 1
        assert results[0].email == "y"


    def test_filter_items_between_operator(self, clean_database):
        """Tests filter_items() with the 'between' operator shorthand"""
        # Arrange
        clean_database.add_item(name="low", age=3, email="a")
        clean_database.add_item(name="mid", age=10, email="b")
        clean_database.add_item(name="high", age=20, email="c")

        # Act — age between 6 and 15 inclusive
        results = clean_database.filter_items({"age": ("between", (6, 15))})

        # Assert
        assert len(results) == 1
        assert results[0].name == "mid"


    def test_filter_items_between_invalid_value_raises(self, clean_database):
        """Tests that 'between' raises ValueError when given a non-2-element value"""
        clean_database.add_item(name="coffee", age=3, email="food")

        with pytest.raises(ValueError):
            clean_database.filter_items({"age": ("between", 10)})


    def test_filter_items_invalid_operator_in_list_raises(self, clean_database):
        """Tests that an invalid operator inside a list-of-tuples raises ValueError"""
        clean_database.add_item(name="coffee", age=3, email="food")

        with pytest.raises(ValueError):
            clean_database.filter_items({"age": [(">=", 1), ("~=", 10)]})


    def test_to_dataframe(self, clean_database):
        """Tests the to_dataframe() method of the DatabaseManager class"""

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        # Fetch all items from the database
        df = clean_database.to_dataframe()
        assert len(df) == 3, "DataFrame does not contain the expected number of items."
        assert df.iloc[0]["name"] == TEST_ENTRY_1["name"], f"Item 1 name does not match {df.iloc[0]["name"]}."
        assert df.iloc[1]["name"] == TEST_ENTRY_2["name"], f"Item 2 name does not match {df.iloc[1]["name"]}."
        assert df.iloc[2]["name"] == TEST_ENTRY_3["name"], f"Item 3 name does not match {df.iloc[2]["name"]}."

    
    def test_update_item(self, clean_database):
        """Tests the update_item() method of the DatabaseManager class"""

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        # Update the item in the database
        clean_database.update_item(1, **TEST_ENTRY_2)

        updated_item = clean_database.fetch_item_by_id(1)

        assert updated_item.name == "Jane Doe", f"Item name not updated correctly: {updated_item.name}"
        assert updated_item.age == 25, f"Item age not updated correctly: {updated_item.age}"
    

    def test_delete_item(self, clean_database):
        """Tests the delete_item() method of the DatabaseManager class"""

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        # Delete the item from the database
        clean_database.delete_item(1)

        assert clean_database.session.query(MockTableObject).count() == 0, "Item not deleted from the database."

    
    def test_delete_items_by_attribute(self, clean_database):
        """Tests the delete_items_by_attribute() method of the DatabaseManager class"""

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        # Delete items by attribute
        clean_database.delete_items_by_attribute(age=30)

        assert clean_database.session.query(MockTableObject).count() == 1, "Items not deleted by attribute."
        remaining_ages = [item.age for item in clean_database.fetch_all_items()]
        assert 30 not in remaining_ages, "Item with specified attribute not deleted."

    
    def test_delete_items_by_filter(self, clean_database):
        """Tests the delete_items_by_filter() method of the DatabaseManager class"""

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        # Delete items by filter
        clean_database.delete_items_by_filter({"age": (">=", 27), "name": "John Doe"})

        assert clean_database.session.query(MockTableObject).count() == 2, "Items not deleted by filter."
        remaining_names = [item.name for item in clean_database.fetch_all_items()]
        assert "John Doe" not in remaining_names, "Item with specified filter not deleted."
        assert "Alice Smith" in remaining_names, "Incorrect item deleted."
        

    def test_clear_table(self, clean_database):
        """Tests the clear_table() method of the DatabaseManager class"""

        # Add multiple items to the database
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        clean_database.clear_table()

        assert clean_database.session.query(MockTableObject).count() == 0, "Table not cleared successfully."

    
    def test_df_columns_match_true(self, clean_database):
        """Tests if the DataFrame columns match the database table columns"""

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        # Fetch all items from the database as a DataFrame
        df = clean_database.to_dataframe()

        # Check if the DataFrame columns match the database table columns
        assert clean_database._df_columns_match(df), "DataFrame columns do not match database table columns."


    def test_dict_columns_match_true(self, clean_database):
        """Tests if the DataFrame columns match the database table columns"""

        # Add an item to the database
        clean_database.add_item(**TEST_ENTRY_1)

        # Check if the DataFrame columns match the database table columns
        assert clean_database._dict_columns_match(TEST_ENTRY_2), "DataFrame columns do not match database table columns."

    
    def test_df_columns_match_false(self, clean_database):
        """Tests if the DataFrame columns match the database table columns"""

        # Add an item with invalid data to the database
        with pytest.raises(TypeError):
            clean_database._df_types_match(INVALID_DF)

        # Check if the DataFrame columns match the database table columns
        assert clean_database.session.query(MockTableObject).count() == 0, "DataFrame columns match database table columns."


    def test_dict_columns_match_false(self, clean_database):
        """Tests if the DataFrame columns match the database table columns"""

        # Add an item with invalid data to the database
        with pytest.raises(TypeError):
            clean_database._dict_types_match(INVALID_ENTRY)

        # Check if the DataFrame columns match the database table columns
        assert clean_database.session.query(MockTableObject).count() == 0, "DataFrame columns match database table columns."


    # --- fetch_item_by_id ---

    def test_fetch_item_by_id_not_found_raises(self, clean_database):
        """Tests that fetch_item_by_id raises ItemNotFoundError when the ID does not exist"""
        with pytest.raises(ItemNotFoundError):
            clean_database.fetch_item_by_id(999)


    # --- upsert ---

    def test_upsert_inserts_new_item(self, clean_database):
        """Tests that upsert creates a new item when no match is found"""
        clean_database.upsert({"name": "John Doe"}, age=30, email="john.doe@email.com")

        assert clean_database.session.query(MockTableObject).count() == 1
        item = clean_database.session.query(MockTableObject).first()
        assert item.name == "John Doe"
        assert item.age == 30


    def test_upsert_updates_existing_item(self, clean_database):
        """Tests that upsert updates an existing item when a match is found"""
        clean_database.add_item(**TEST_ENTRY_1)

        clean_database.upsert({"name": TEST_ENTRY_1["name"]}, age=99, email="updated@email.com")

        assert clean_database.session.query(MockTableObject).count() == 1
        item = clean_database.session.query(MockTableObject).first()
        assert item.age == 99
        assert item.email == "updated@email.com"


    # --- count_items ---

    def test_count_items_all(self, clean_database):
        """Tests count_items with no filter returns total row count"""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        assert clean_database.count_items() == 2


    def test_count_items_with_attribute(self, clean_database):
        """Tests count_items with a keyword filter"""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        assert clean_database.count_items(age=30) == 2


    def test_count_items_empty(self, clean_database):
        """Tests count_items returns 0 when no items match"""
        clean_database.add_item(**TEST_ENTRY_1)

        assert clean_database.count_items(age=999) == 0


    # --- exists ---

    def test_exists_true(self, clean_database):
        """Tests that exists returns True when a matching item is present"""
        clean_database.add_item(**TEST_ENTRY_1)

        assert clean_database.exists(name=TEST_ENTRY_1["name"]) is True


    def test_exists_false(self, clean_database):
        """Tests that exists returns False when no matching item is present"""
        assert clean_database.exists(name="ghost") is False


    # --- context manager ---

    def test_context_manager_closes_session(self):
        """Tests that the context manager automatically calls end_session on exit"""
        db_file_cm = DatabaseFile("cm_test.db")
        try:
            with DatabaseManager(MockTableObject, db_file_cm) as db:
                db.add_item(**TEST_ENTRY_1)
                assert db.session.query(MockTableObject).count() == 1

            # After the with block, the session should be closed
            assert db.session.is_active is False or db.engine is not None
        finally:
            db_file_cm.delete()


    # --- ilike operator ---

    def test_filter_items_ilike(self, clean_database):
        """Tests the ilike (case-insensitive LIKE) operator in filter_items"""
        clean_database.add_item(name="Alpha", age=1, email="alpha@test.com")
        clean_database.add_item(name="Beta", age=2, email="beta@test.com")
        clean_database.add_item(name="ALPHA_UPPER", age=3, email="upper@test.com")

        results = clean_database.filter_items({"name": ("ilike", "alpha%")})

        assert len(results) == 2
        names = {r.name for r in results}
        assert "Alpha" in names
        assert "ALPHA_UPPER" in names


    # --- add_multiple_items ---

    def test_add_multiple_items(self, clean_database):
        """Tests that add_multiple_items() inserts all entries"""
        clean_database.add_multiple_items([TEST_ENTRY_1, TEST_ENTRY_2, TEST_ENTRY_3])

        assert clean_database.session.query(MockTableObject).count() == 3
        names = {item.name for item in clean_database.fetch_all_items()}
        assert names == {TEST_ENTRY_1["name"], TEST_ENTRY_2["name"], TEST_ENTRY_3["name"]}


    # --- filter_items: additional operators ---

    def test_filter_items_not_equal(self, clean_database):
        """Tests the != operator in filter_items"""
        clean_database.add_item(**TEST_ENTRY_1)  # age 30
        clean_database.add_item(**TEST_ENTRY_2)  # age 25

        results = clean_database.filter_items({"age": ("!=", 30)})

        assert len(results) == 1
        assert results[0].age == 25


    def test_filter_items_in_operator(self, clean_database):
        """Tests the 'in' operator in filter_items"""
        clean_database.add_item(**TEST_ENTRY_1)  # John Doe
        clean_database.add_item(**TEST_ENTRY_2)  # Jane Doe
        clean_database.add_item(**TEST_ENTRY_3)  # Alice Smith

        results = clean_database.filter_items({"name": ("in", ["John Doe", "Alice Smith"])})

        assert len(results) == 2
        names = {r.name for r in results}
        assert names == {"John Doe", "Alice Smith"}


    def test_filter_items_like_operator(self, clean_database):
        """Tests the 'like' (case-sensitive LIKE) operator in filter_items"""
        clean_database.add_item(**TEST_ENTRY_1)  # John Doe
        clean_database.add_item(**TEST_ENTRY_2)  # Jane Doe
        clean_database.add_item(**TEST_ENTRY_3)  # Alice Smith

        results = clean_database.filter_items({"name": ("like", "%Doe")})

        assert len(results) == 2
        names = {r.name for r in results}
        assert names == {"John Doe", "Jane Doe"}


    # --- filter_items use_or=True ---

    def test_filter_items_or_logic(self, clean_database):
        """Tests that use_or=True returns rows matching ANY filter (OR), not ALL (AND)"""
        clean_database.add_item(**TEST_ENTRY_1)  # John Doe, age 30
        clean_database.add_item(**TEST_ENTRY_2)  # Jane Doe, age 25
        clean_database.add_item(**TEST_ENTRY_3)  # Alice Smith, age 30

        # OR: name == "John Doe" OR age == 25
        # Matches John (name match) and Jane (age match); Alice matches neither
        results = clean_database.filter_items({"name": "John Doe", "age": 25}, use_or=True)

        assert len(results) == 2
        names = {r.name for r in results}
        assert "John Doe" in names
        assert "Jane Doe" in names
        assert "Alice Smith" not in names


    # --- delete_items_by_filter use_or=True ---

    def test_delete_items_by_filter_or_logic(self, clean_database):
        """Tests that delete_items_by_filter(use_or=True) deletes rows matching ANY filter"""
        clean_database.add_item(**TEST_ENTRY_1)  # John Doe, age 30
        clean_database.add_item(**TEST_ENTRY_2)  # Jane Doe, age 25
        clean_database.add_item(**TEST_ENTRY_3)  # Alice Smith, age 30

        # OR: age <= 25 OR name == "Alice Smith"
        # Deletes: Jane (age 25) and Alice (name match); John survives
        clean_database.delete_items_by_filter({"age": ("<=", 25), "name": "Alice Smith"}, use_or=True)

        assert clean_database.session.query(MockTableObject).count() == 1
        assert clean_database.fetch_all_items()[0].name == "John Doe"


    # --- fetch_all_items empty ---

    def test_fetch_all_items_empty(self, clean_database):
        """Tests that fetch_all_items() returns an empty list when the table has no rows"""
        result = clean_database.fetch_all_items()
        assert result == []


    # --- fetch_items_by_attribute no matches ---

    def test_fetch_items_by_attribute_no_matches(self, clean_database):
        """Tests that fetch_items_by_attribute() returns an empty list when no rows match"""
        clean_database.add_item(**TEST_ENTRY_1)
        result = clean_database.fetch_items_by_attribute(name="ghost")
        assert result == []


    # --- update_item error paths ---

    def test_update_item_not_found_raises(self, clean_database):
        """Tests that update_item() raises ItemNotFoundError when the ID doesn't exist"""
        with pytest.raises(ItemNotFoundError):
            clean_database.update_item(999, name="nobody")


    def test_update_item_duplicate_raises(self, clean_database):
        """Tests that update_item() raises DatabaseIntegrityError on a UNIQUE violation"""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        with pytest.raises(DatabaseIntegrityError) as exc_info:
            clean_database.update_item(1, email=TEST_ENTRY_2["email"])

        assert exc_info.value.column == "email"


    # --- delete_item error path ---

    def test_delete_item_not_found_raises(self, clean_database):
        """Tests that delete_item() raises ItemNotFoundError when the ID doesn't exist"""
        with pytest.raises(ItemNotFoundError):
            clean_database.delete_item(999)


    # --- append_dataframe duplicate ---

    def test_append_dataframe_duplicate_raises(self, clean_database):
        """
        Tests that append_dataframe() raises an error on a UNIQUE violation.

        Note: df.to_sql() executes before the session.flush() try/except block in
        append_dataframe(), so the IntegrityError is caught by pandas and wrapped as
        pd.errors.DatabaseError rather than our custom DatabaseIntegrityError.
        """
        clean_database.add_item(**TEST_ENTRY_1)

        with pytest.raises(pd.errors.DatabaseError):
            clean_database.append_dataframe(pd.DataFrame([TEST_ENTRY_1]))


    # --- validation helpers: column mismatch ---

    def test_df_columns_match_false_raises_value_error(self, clean_database):
        """Tests that _df_columns_match() raises ValueError when the DataFrame has unknown columns"""
        bad_df = pd.DataFrame([{"nonexistent": "x", "another_bad": "y"}])
        with pytest.raises(ValueError):
            clean_database._df_columns_match(bad_df)


    def test_dict_columns_match_false_raises_value_error(self, clean_database):
        """Tests that _dict_columns_match() raises ValueError when the dict has unknown keys"""
        with pytest.raises(ValueError):
            clean_database._dict_columns_match({"nonexistent": "x"})


    # --- convert_orm_list_to_dataframe ---

    def test_convert_orm_list_to_dataframe(self, clean_database):
        """Tests that convert_orm_list_to_dataframe() converts ORM objects to a DataFrame"""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        orm_list = clean_database.fetch_all_items()
        df = clean_database.convert_orm_list_to_dataframe(orm_list)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert set(["id", "name", "age", "email"]).issubset(set(df.columns))
        assert list(df["name"]) == [TEST_ENTRY_1["name"], TEST_ENTRY_2["name"]]


dt_db_file = DatabaseFile("dt_test.db")


@pytest.fixture
def clean_datetime_database():
    """Fixture providing a DatetimeMockTableObject manager with a clean in-memory table."""
    db_manager = DatabaseManager(DatetimeMockTableObject, dt_db_file)

    try:
        db_manager.session.query(DatetimeMockTableObject).delete()
        db_manager.session.commit()
        yield db_manager
    except Exception:
        db_manager.session.rollback()
        raise
    finally:
        db_manager.end_session()
        time.sleep(0.1)
        dt_db_file.delete()


class TestDatetimeFiltering:
    """Tests filter_items() against a DateTime column, reproducing the budgy date-range bug."""

    def test_filter_datetime_range_list_of_tuples(self, clean_datetime_database):
        """
        Reproduces the core budgy bug: filtering a DateTime column with a list of
        (operator, datetime) tuples should generate a >= / <= range query, not an
        equality check that passes the list as a raw parameter.
        """
        db = clean_datetime_database
        db.add_item(**DATE_ENTRY_1)  # Jan 5 12:00
        db.add_item(**DATE_ENTRY_2)  # Feb 10 05:00
        db.add_item(**DATE_ENTRY_3)  # Mar 21 16:00

        from datetime import datetime
        start = datetime(2024, 1, 1)
        end   = datetime(2024, 2, 28, 23, 59, 59)

        results = clean_datetime_database.filter_items({
            "accessed_timestamp": [(">=", start), ("<=", end)]
        })

        assert len(results) == 2
        names = {r.name for r in results}
        assert "John" in names
        assert "Mimi" in names
        assert "Gia" not in names

    def test_filter_datetime_range_combined_with_equality(self, clean_datetime_database):
        """
        Reproduces the full budgy query pattern:
            attributes = {k: ("==", v) for k, v in kwargs.items()}
            attributes["authorized_date"] = [(">=", start_date), ("<=", end_date)]
            attributes["exclude"]         = ("==", False)

        Here we use the `name` column as the extra equality constraint (stand-in for exclude).
        Both the datetime range AND the equality filter must be applied correctly.
        """
        db = clean_datetime_database
        db.add_item(**DATE_ENTRY_1)  # Jan  5, name="John"
        db.add_item(**DATE_ENTRY_2)  # Feb 10, name="Mimi"
        db.add_item(**DATE_ENTRY_3)  # Mar 21, name="Gia"

        from datetime import datetime
        start = datetime(2024, 1, 1)
        end   = datetime(2024, 3, 31, 23, 59, 59)

        results = clean_datetime_database.filter_items({
            "accessed_timestamp": [(">=", start), ("<=", end)],
            "name": ("==", "Mimi"),
        })

        assert len(results) == 1
        assert results[0].name == "Mimi"


    def test_switched_date_entry_raises(self, clean_datetime_database):
        """Tests that inserting SWITCHED_DATE_ENTRY (datetime for Date column, date for DateTime) raises TypeError"""
        with pytest.raises(TypeError):
            clean_datetime_database._dict_compatible(SWITCHED_DATE_ENTRY)


class TestQuery:
    """Tests the query() method of DatabaseManager."""

    # --- Slice 1: bare query() ---

    def test_query_all_columns_returns_dataframe(self, clean_database):
        """query() with no args returns a DataFrame containing all rows and columns."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        result = clean_database.query()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert set(["id", "name", "age", "email"]).issubset(set(result.columns))

    def test_query_empty_table_returns_empty_dataframe(self, clean_database):
        """query() on an empty table returns an empty DataFrame (not raises)."""
        result = clean_database.query()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_query_specific_columns_subset(self, clean_database):
        """query(columns=[...]) returns only the requested columns."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        result = clean_database.query(columns=["name", "age"])

        assert list(result.columns) == ["name", "age"]
        assert len(result) == 2

    def test_query_single_column(self, clean_database):
        """query(columns=['email']) returns a single-column DataFrame."""
        clean_database.add_item(**TEST_ENTRY_1)

        result = clean_database.query(columns=["email"])

        assert list(result.columns) == ["email"]
        assert result.iloc[0]["email"] == TEST_ENTRY_1["email"]

    def test_query_empty_table_specific_columns_preserves_column_names(self, clean_database):
        """query(columns=[...]) on empty table returns empty DataFrame with correct columns."""
        result = clean_database.query(columns=["name"])

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name"]
        assert len(result) == 0

    def test_query_invalid_column_raises(self, clean_database):
        """query(columns=['nonexistent']) raises ValueError."""
        with pytest.raises(ValueError, match="nonexistent"):
            clean_database.query(columns=["nonexistent"])

    def test_query_empty_columns_list_raises(self, clean_database):
        """query(columns=[]) raises ValueError."""
        with pytest.raises(ValueError):
            clean_database.query(columns=[])

    def test_query_filter_equality(self, clean_database):
        """filters={"age": 30} returns 2 matching rows."""
        clean_database.add_item(**TEST_ENTRY_1)  # age 30
        clean_database.add_item(**TEST_ENTRY_2)  # age 25
        clean_database.add_item(**TEST_ENTRY_3)  # age 30

        result = clean_database.query(filters={"age": 30})

        assert len(result) == 2

    def test_query_filter_operator(self, clean_database):
        """filters with > operator returns matching rows."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        result = clean_database.query(filters={"age": (">", 25)})

        assert len(result) == 2
        assert all(result["age"] > 25)

    def test_query_filter_between(self, clean_database):
        """between operator returns only rows in range."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        result = clean_database.query(filters={"age": ("between", (24, 29))})

        assert len(result) == 1
        assert result.iloc[0]["name"] == TEST_ENTRY_2["name"]

    def test_query_filter_list_of_tuples(self, clean_database):
        """list of tuples applies multiple constraints on one column."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        result = clean_database.query(filters={"age": [(">=", 25), ("<=", 30)]})

        assert len(result) == 3

    def test_query_filter_no_matches(self, clean_database):
        """Non-matching filter returns empty DataFrame."""
        clean_database.add_item(**TEST_ENTRY_1)

        result = clean_database.query(filters={"age": 999})

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_query_filter_invalid_column_raises(self, clean_database):
        """filters with a non-existent column raises AttributeError (from _build_filter_clauses)."""
        with pytest.raises(AttributeError):
            clean_database.query(filters={"bad_col": "x"})

    def test_query_filter_with_column_selection(self, clean_database):
        """Column selection and filtering can be combined."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        result = clean_database.query(columns=["name"], filters={"age": 30})

        assert list(result.columns) == ["name"]
        assert len(result) == 2

    def test_query_order_by_string_ascending(self, clean_database):
        """order_by='name' sorts rows A-Z."""
        clean_database.add_item(**TEST_ENTRY_1)  # John Doe
        clean_database.add_item(**TEST_ENTRY_2)  # Jane Doe
        clean_database.add_item(**TEST_ENTRY_3)  # Alice Smith

        result = clean_database.query(columns=["name"], order_by="name")

        assert list(result["name"]) == ["Alice Smith", "Jane Doe", "John Doe"]

    def test_query_order_by_string_descending(self, clean_database):
        """order_by='name', ascending=False sorts rows Z-A."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        result = clean_database.query(columns=["name"], order_by="name", ascending=False)

        assert list(result["name"]) == ["John Doe", "Jane Doe", "Alice Smith"]

    def test_query_order_by_single_tuple_desc(self, clean_database):
        """order_by=('age', 'desc') puts highest ages first."""
        clean_database.add_item(**TEST_ENTRY_1)  # age 30
        clean_database.add_item(**TEST_ENTRY_2)  # age 25
        clean_database.add_item(**TEST_ENTRY_3)  # age 30

        result = clean_database.query(columns=["age"], order_by=("age", "desc"))

        assert result.iloc[0]["age"] == 30
        assert result.iloc[-1]["age"] == 25

    def test_query_order_by_list_of_tuples(self, clean_database):
        """Multi-column sort: age asc, then name asc — Alice before John (both age 30)."""
        clean_database.add_item(**TEST_ENTRY_1)  # John, 30
        clean_database.add_item(**TEST_ENTRY_2)  # Jane, 25
        clean_database.add_item(**TEST_ENTRY_3)  # Alice, 30

        result = clean_database.query(
            columns=["name", "age"],
            order_by=[("age", "asc"), ("name", "asc")]
        )

        assert list(result["name"]) == ["Jane Doe", "Alice Smith", "John Doe"]

    def test_query_order_by_case_insensitive_direction(self, clean_database):
        """order_by direction string is case-insensitive ('DESC' == 'desc')."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        result = clean_database.query(columns=["age"], order_by=("age", "DESC"))

        assert result.iloc[0]["age"] == 30

    def test_query_order_by_invalid_column_raises(self, clean_database):
        """order_by with a non-existent column raises ValueError."""
        with pytest.raises(ValueError, match="nonexistent"):
            clean_database.query(order_by="nonexistent")

    def test_query_order_by_invalid_direction_raises(self, clean_database):
        """order_by with an invalid direction raises ValueError."""
        with pytest.raises(ValueError, match="direction"):
            clean_database.query(order_by=("age", "downward"))

    def test_query_order_by_single_element_tuple_raises(self, clean_database):
        """order_by=('age',) — 1-element tuple — raises ValueError."""
        with pytest.raises(ValueError):
            clean_database.query(order_by=("age",))

    def test_query_limit_one(self, clean_database):
        """limit=1 returns exactly 1 row."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        result = clean_database.query(limit=1)

        assert len(result) == 1

    def test_query_limit_exceeds_rows(self, clean_database):
        """limit larger than row count returns all rows without error."""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        result = clean_database.query(limit=100)

        assert len(result) == 2

    def test_query_offset(self, clean_database):
        """offset=1 with sorting skips the first sorted row."""
        clean_database.add_item(**TEST_ENTRY_1)  # John Doe
        clean_database.add_item(**TEST_ENTRY_2)  # Jane Doe
        clean_database.add_item(**TEST_ENTRY_3)  # Alice Smith

        result = clean_database.query(columns=["name"], order_by="name", offset=1)

        # Sorted: Alice, Jane, John — skip Alice
        assert list(result["name"]) == ["Jane Doe", "John Doe"]

    def test_query_limit_and_offset(self, clean_database):
        """limit=1, offset=1 returns exactly the second sorted row."""
        clean_database.add_item(**TEST_ENTRY_1)  # John Doe
        clean_database.add_item(**TEST_ENTRY_2)  # Jane Doe
        clean_database.add_item(**TEST_ENTRY_3)  # Alice Smith

        result = clean_database.query(columns=["name"], order_by="name", limit=1, offset=1)

        # Sorted: Alice, Jane, John — skip Alice, take Jane
        assert len(result) == 1
        assert result.iloc[0]["name"] == "Jane Doe"

    def test_query_offset_beyond_rows(self, clean_database):
        """offset beyond total row count returns empty DataFrame."""
        clean_database.add_item(**TEST_ENTRY_1)

        result = clean_database.query(offset=100)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_query_columns_filter_sort(self, clean_database):
        """Column selection, filter, and sort work together correctly."""
        clean_database.add_item(**TEST_ENTRY_1)  # John, 30
        clean_database.add_item(**TEST_ENTRY_2)  # Jane, 25
        clean_database.add_item(**TEST_ENTRY_3)  # Alice, 30

        result = clean_database.query(
            columns=["name", "age"],
            filters={"age": 30},
            order_by="name",
        )

        assert list(result.columns) == ["name", "age"]
        assert len(result) == 2
        assert list(result["name"]) == ["Alice Smith", "John Doe"]

    def test_query_filter_sort_paginate(self, clean_database):
        """Sort applies before pagination: filter to 2 rows, sort, take only first."""
        clean_database.add_item(**TEST_ENTRY_1)  # John, 30
        clean_database.add_item(**TEST_ENTRY_2)  # Jane, 25
        clean_database.add_item(**TEST_ENTRY_3)  # Alice, 30

        # Filter: age == 30 → John, Alice; Sort by name asc → Alice, John; limit 1 → Alice
        result = clean_database.query(
            columns=["name"],
            filters={"age": 30},
            order_by="name",
            limit=1,
        )

        assert len(result) == 1
        assert result.iloc[0]["name"] == "Alice Smith"

    def test_query_all_params(self, clean_database):
        """All parameters combined: columns + filter + order_by + limit."""
        clean_database.add_item(**TEST_ENTRY_1)  # John, 30
        clean_database.add_item(**TEST_ENTRY_2)  # Jane, 25
        clean_database.add_item(**TEST_ENTRY_3)  # Alice, 30

        result = clean_database.query(
            columns=["name", "age"],
            filters={"age": 30},
            order_by="name",
            limit=1,
        )

        assert list(result.columns) == ["name", "age"]
        assert len(result) == 1
        assert result.iloc[0]["name"] == "Alice Smith"


class TestQuerySearch:
    """Tests the search parameter of query()"""

    # --- Cycle 1: basic match ---

    def test_search_finds_match(self, clean_database):
        """search returns rows where any string column contains the term"""
        clean_database.add_item(**TEST_ENTRY_1)  # name="John Doe", email="john.doe@email.com"
        clean_database.add_item(**TEST_ENTRY_2)  # name="Jane Doe", email="jane.doe@email.com"

        result = clean_database.query(search="John")

        assert len(result) == 1
        assert result.iloc[0]["name"] == "John Doe"

    # --- Cycle 2: no match ---

    def test_search_no_match_returns_empty(self, clean_database):
        """search returns an empty DataFrame when no row contains the term"""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)

        result = clean_database.query(search="zzznomatch")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    # --- Cycle 3: case insensitivity ---

    def test_search_case_insensitive(self, clean_database):
        """search is case-insensitive: uppercase term matches lowercase data"""
        clean_database.add_item(**TEST_ENTRY_3)  # name="Alice Smith"

        result = clean_database.query(search="ALICE")

        assert len(result) == 1
        assert result.iloc[0]["name"] == "Alice Smith"

    # --- Cycle 4: OR across columns ---

    def test_search_matches_any_column(self, clean_database):
        """search matches if term appears in any string column (OR logic)"""
        clean_database.add_item(**TEST_ENTRY_1)  # name="John Doe", email="john.doe@email.com"
        clean_database.add_item(**TEST_ENTRY_3)  # name="Alice Smith", email="alice.smith@email.com"

        # "john.doe" only appears in the email column, not the name column
        result = clean_database.query(search="john.doe")

        assert len(result) == 1
        assert result.iloc[0]["name"] == "John Doe"

    # --- Cycle 6: explicit search_columns ---

    def test_search_explicit_columns(self, clean_database):
        """search_columns limits search scope; match in excluded column is not returned"""
        clean_database.add_item(**TEST_ENTRY_1)  # name="John Doe", email="john.doe@email.com"

        # "john.doe" is in email but we restrict search to name only → no match
        result = clean_database.query(search="john.doe", search_columns=["name"])

        assert len(result) == 0

    # --- Cycle 7: invalid column name raises ---

    def test_search_invalid_column_raises(self, clean_database):
        """search_columns with a non-existent column raises ValueError"""
        with pytest.raises(ValueError):
            clean_database.query(search="John", search_columns=["nonexistent_col"])

    # --- Cycle 8: non-string column raises ---

    def test_search_non_string_column_raises(self, clean_database):
        """search_columns with a non-string column (e.g. age) raises ValueError"""
        with pytest.raises(ValueError):
            clean_database.query(search="30", search_columns=["age"])

    # --- Cycle 9: search=None regression ---

    def test_search_none_does_not_change_behavior(self, clean_database):
        """omitting search returns all rows, same as before the feature existed"""
        clean_database.add_item(**TEST_ENTRY_1)
        clean_database.add_item(**TEST_ENTRY_2)
        clean_database.add_item(**TEST_ENTRY_3)

        result = clean_database.query(search=None)

        assert len(result) == 3

    # --- Cycle 5: AND with filters ---

    def test_search_with_filters(self, clean_database):
        """search AND filters must both match; filter alone is not enough"""
        clean_database.add_item(**TEST_ENTRY_1)  # name="John Doe", age=30
        clean_database.add_item(**TEST_ENTRY_2)  # name="Jane Doe", age=25
        # Both contain "Doe" in name — search matches both.
        # Only TEST_ENTRY_1 has age=30 — filter reduces to 1.

        result = clean_database.query(search="Doe", filters={"age": 30})

        assert len(result) == 1
        assert result.iloc[0]["name"] == "John Doe"
