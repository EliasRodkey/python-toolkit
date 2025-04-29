#!python3
'''
local_db_handler.database_manader.py

This module contains a database object class

Classes:
    - LocalDB: a class object which allows for the following actions to be performed:
        - Creation
        - Reading
        - Editing
        - Updating
        - Deletion

    - LocalDB functions:
        - 
'''

# Initiate module logger
from . import Logger, ELF

# Third-Party library imports
import pandas as pd
from typing import List

# local imports
from local_db.database_connections import create_engine_conn, create_session
from local_db.database_file import DatabaseFile
from local_db.utils import map_dtype_list_to_sql


# Initialize module logger
_logger = Logger('database_manager')
_logger.add_file_handler(format=ELF.FORMAT_LOGGER_NAME)



class DatabaseManager():
    '''
    Generic database manager wrapper class that allows for simple database operations to be performed on a local database file.
    '''

    def __init__(self, table_class, database_file: DatabaseFile):
        '''
        Initializes the DatabaseManager with a SQLAlchemy session and a database object class.

        Args:
            table_class (BaseTable child class): The SQLAlchemy ORM class representing the database table. (class not instance)
            database_file (class): The DatabaseFile object representing the database file to be used.
        '''

        # Initialize the database file and object class
        self.file = database_file
        self.table_class = table_class
        
        # Create database session using DatabaseFile file_path attribute
        self.start_session()
        self.table_class.metadata.create_all(self.engine)
        

    def add_item(self, **kwargs):
        '''
        Adds a new item to the database. unpack a dictionary if attributes using '**' operator

        Args:
            **kwargs: Keyword arguments representing the attributes of the item to be added.
        '''

        # Check to make sure the dictionary keys match the database table columns
        if self._dict_compatible(kwargs):

            # Create a new instance of the database object class with the provided attributes
            new_item = self.table_class(**kwargs)

            # Add the new item to the session and commit the changes to the database
            self.session.add(new_item)
        
            # Commit the changes to the database
            self.session.commit()

            _logger.info(f'Item added to database: {self.table_class.__tablename__} with attributes: {kwargs}')
    

    def add_multiple_items(self, entries: List[dict]):
        '''
        Adds a new item to the database. unpack a dictionary if attributes using '**' operator

        Args:
            **kwargs: Keyword arguments representing the attributes of the item to be added.
        '''

        # Create a new instance of the database object class with the provided attributes
        for entry in entries:
            self.add_item(entry)

        # Commit the changes to the database
        self.session.commit()


    def append_dataframe(self, df):
        '''
        Appends a pandas DataFrame to the database table.

        Args:
            df (pd.DataFrame): The DataFrame to be appended to the database table.
        '''

        # Check to make sure the dataframe columns match the database table columns
        if self._df_compatible(df):

            # Append the DataFrame to the database table using the SQLAlchemy engine
            df.to_sql(self.table_class.__tablename__, self.engine, if_exists='append', index=False)
        
            # Commit the changes to the database
            self.session.commit()

            _logger.info(f'DataFrame appended to database: {self.table_class.__tablename__} with attributes: {df.columns.tolist()}')


    def fetch_all_items(self):
        '''
        Fetches all items from the database table
        
        Returns:
            list: A list of all items in the database table.
        '''
        return self.session.query(self.table_class).all()
    

    def fetch_item_by_id(self, item_id):
        '''
        Fetches an item from the database based on its ID.
        
        Args:
            item_id (int): The ID of the item to be fetched.

        Returns:
            item: The item object if found, otherwise None.
        '''

        # Locate the item in the database using its ID
        item = self.session.query(self.table_class).filter_by(id=item_id).first()

        # If the item exists, return it; otherwise, return None
        if item:
            return item
        else:
            return None
    

    def fetch_items_by_attribute(self, **kwargs):
        '''
        Fetches items from the database based on specified attributes.
        
        Args:
            **kwargs: Keyword arguments representing the attributes to filter by.

        Returns:
            list: A list of items matching the specified attributes.
        '''

        # Create a query object to filter items based on the provided attributes
        query = self.session.query(self.table_class).filter_by(**kwargs)

        if query:
            # If the query returns results, return them as a list
            return query.all()
        else:
            # If no results are found, return an empty list
            return []

    
    def to_dataframe(self):
        '''
        Converts the database table to a pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing all items in the database table.
        '''

        # Fetch all items from the database and convert them to a DataFrame
        return pd.read_sql(self.session.query(self.table_class).statement, self.session.bind)
    

    def update_item(self, item_id, **kwargs):
        '''
        Updates an item in the database based on its ID.

        Args:
            item_id (int): The ID of the item to be updated.
            **kwargs: Keyword arguments representing the attributes to be updated.
        '''

        ## Check to make sure the dictionary keys match the database table columns
        if self._dict_columns_match(kwargs):
            
            # Locate the item in the database using its ID
            item = self.session.query(self.table_class).filter_by(id=item_id).first()

            # If the item exists, update its attributes and commit the changes to the database
            if item:

                # Unpack the keyword arguments and update the item's attributes
                for key, value in kwargs.items():
                    if hasattr(item, key): # Check if the attribute exists in the item
                        setattr(item, key, value)

                # Commit the changes to the database
                self.session.commit()


    def delete_item(self, item_id):
        '''
        Deletes an item from the database based on its ID.
        
        Args:
            item_id (int): The ID of the item to be deleted.
        '''

        # Locate the item in the database using its ID
        item = self.session.query(self.table_class).filter_by(id=item_id).first()

        # If the item exists, delete it from the session and commit the changes to the database
        if item:
            self.session.delete(item)
            self.session.commit()


    def start_session(self):
        '''Starts a new database session.'''

        # Create a new session using the engine connection
        self.engine = create_engine_conn(self.file.file_path)
        self.session = create_session(self.engine)
        _logger.info(f'DatabaseManager session started with file: {self.file.name} and class type: {self.table_class}')
        _logger.debug(f'DatabaseManager.start_session() -> session started with file {self.file.abspath} and object class type: {self.table_class}')


    def end_session(self):
        '''Ends the database session and closes the connection.'''

        # Close the session and dispose of the engine connection
        self.session.close()
        self.engine.dispose()
        _logger.info(f'DatabaseManager connection closed with file: {self.file.name} and class type: {self.table_class}')
        _logger.debug(f'DatabaseManager.end_session() -> connection closed with file {self.file.abspath} and object class type: {self.table_class}')
    

    def _df_columns_match(self, df: pd.DataFrame) -> bool:
        '''
        Checks if the columns of the input data match the columns of the database table.

        Args:
            database_input (pd.DataFrame): The input data to be checked.

        Returns:
            bool: True if the columns match, False otherwise.
        '''

        # Check if the columns of the input data match the columns of the database table
        columns_match = set(df.columns).issubset(set(self.table_class.get_column_names()))

        if columns_match:
            _logger.debug(f'DatabaseManager._check_df_columns_match() -> DataFrame columns match database table columns: {df.columns.tolist()}')
            return columns_match
        else:
            # Raise ValueError if they do not match
            _logger.error(f'DatabaseManager._check_df_columns_match() -> DataFrame columns do not match database table columns: {df.columns.tolist()}')
            raise ValueError(f'DataFrame columns do not match database table columns: {df.columns.tolist()}')
    

    def _df_types_match(self, df: pd.DataFrame) -> bool:
        '''
        Checks if the data types of the input DataFrame match the data types of the database table.

        Args:
            df (pd.DataFrame): The input DataFrame to be checked.
        
        Returns:
            bool: True if the data types match, False otherwise.
        '''
        # Map the data types of the DataFrame to SQLAlchemy types
        sql_datatypes = map_dtype_list_to_sql(df.dtypes.tolist())
        sql_datatypes_dict = {}
        for i, column in enumerate(df.columns.tolist()):
            sql_datatypes_dict[column] = sql_datatypes[i]

        # Get the data types of the database table columns
        table_datatypes_set = set(self.table_class.get_column_types().items())

        # Check if the data types of the input DataFrame match the data types of the database table
        types_match = set(sql_datatypes_dict.items()).issubset(set(table_datatypes_set))

        if types_match:
            _logger.debug(f'DatabaseManager._check_df_types_match() -> DataFrame types match database table types: {sql_datatypes}')
            return types_match
        else:
            # Raise ValueError if they do not match
            _logger.error(f'DatabaseManager._check_df_types_match() -> DataFrame types do not match database table types: {sql_datatypes}')
            raise TypeError(f'DataFrame types do not match database table types: {sql_datatypes}')
    

    def _df_compatible(self, df: pd.DataFrame) -> bool:
        '''
        Checks if the input DataFrame is compatible with the database table.

        Args:
            df (pd.DataFrame): The input DataFrame to be checked.

        Returns:
            bool: True if the DataFrame is compatible, False otherwise.
        '''

        # Check if the columns and data types of the DataFrame match the database table
        return self._df_columns_match(df) and self._df_types_match(df)


    def _dict_columns_match(self, data: dict) -> bool:
        '''
        Checks if the keys of the input dictionary match the columns of the database table.

        Args:
            data (dict): The input dictionary to be checked.

        Returns:
            bool: True if the keys match, False otherwise.
        '''

        # Check if the keys of the input dictionary match the columns of the database table
        columns_match = set(data.keys()).issubset(set(self.table_class.get_column_names()))

        if columns_match:
            _logger.debug(f'DatabaseManager._check_dict_columns_match() -> Dictionary columns match database table columns: {data.keys()}')
            return columns_match
        else:
            # Raise ValueError if they do not match
            _logger.error(f'DatabaseManager._check_dict_columns_match() -> Dictionary columns do not match database table columns: {data.keys()}')
            raise ValueError(f'Dictionary columns do not match database table columns: {data.keys()}')


    def _dict_types_match(self, data: dict) -> bool:
        '''
        Checks if the data types of the input DataFrame match the data types of the database table.

        Args:
            data: The input dict to be checked.
        
        Returns:
            bool: True if the data types match, False otherwise.
        '''
        # Map the data types of the DataFrame to SQLAlchemy types
        sql_datatypes = map_dtype_list_to_sql([pd.Series([value]).dtype for value in data.values()])
        sql_datatypes_dict = {}
        for i, column in enumerate(data.keys()):
            sql_datatypes_dict[column] = sql_datatypes[i]

        # Get the data types of the database table columns
        table_datatypes_set = set(self.table_class.get_column_types().items())

        # Check if the data types of the input DataFrame match the data types of the database table
        types_match = set(sql_datatypes_dict.items()).issubset(set(table_datatypes_set))

        if types_match:
            _logger.debug(f'DatabaseManager._check_dict_types_match() -> Dictionary types match database table types: {sql_datatypes}')
            return types_match
        else:
            # Raise ValueError if they do not match
            _logger.error(f'DatabaseManager._check_dict_types_match() -> Dictionary types do not match database table types: {sql_datatypes}')
            raise TypeError(f'Dictionary types do not match database table types: {sql_datatypes}')
        

    def _dict_compatible(self, data: dict) -> bool:
        '''
        Checks if the input dictionary is compatible with the database table.

        Args:
            data (dict): The input dictionary to be checked.

        Returns:
            bool: True if the dictionary is compatible, False otherwise.
        '''

        # Check if the columns and data types of the DataFrame match the database table
        return self._dict_columns_match(data) and self._dict_types_match(data)
    

if __name__ == "__main__":
    pass