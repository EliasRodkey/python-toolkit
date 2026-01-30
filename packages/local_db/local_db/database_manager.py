#!python3
"""
local_db.database_manager.py

This module contains a database object class.
logger in this module used LoggingExtras.TABLE_CLASS to refer to the current table class name in json logging.

Classes:
    - DatabaseManager: a class object which allows for the following actions to be performed:
        - Creation
        - Reading
        - Editing
        - Updating
        - Deletion
"""
# Standard library imports
from typing import List, Any

# Third-Party library imports
import pandas as pd
import sqlalchemy

# Import logging dependencies
import logging
from loggers import configure_logger

# local imports
from local_db.database_connections import create_engine_conn, create_session
from local_db.base_table import BaseTable
from local_db.database_file import DatabaseFile
from local_db.utils import LoggingExtras, map_dtype_list_to_sql, orm_list_to_dataframe


# Initialize module logger
logger = logging.getLogger(__name__)
configure_logger(logger)



class DatabaseManager():
    """
    Generic Database manager wrapper class that allows for simple database operations to be performed on a local database file.

    Functions:
        - add_item: Adds a new item to the database.
        - add_multiple_items: Adds multiple new items to the database.
        - append_dataframe: Appends a pandas DataFrame to the database table.
        - fetch_all_items: Fetches all items from the database table.
        - fetch_item_by_id: Fetches an item from the database based on its ID.
        - fetch_items_by_attribute: Fetches items from the database based on specified attributes.
        - filter_items: Apply N filters with operators and return ORM objects.
        - to_dataframe: Converts the database table to a pandas DataFrame.
        - update_item: Updates an item in the database based on its ID.
        - delete_item: Deletes an item from the database based on its ID.
        - start_session: Starts a new database session.
        - end_session: Ends the database session and closes the connection.
    """

    def __init__(self, table_class: BaseTable, database_file: DatabaseFile):
        """
        Initializes the DatabaseManager with a SQLAlchemy session and a database object class.

        Args:
            table_class (BaseTable child class): The SQLAlchemy ORM class representing the database table. (class not instance)
            database_file (class): The DatabaseFile object representing the database file to be used.
        """

        # Initialize the database file and object class
        self.file = database_file
        self.table_class = table_class
        self.table_name = self.table_class.__tablename__
        
        # Create database session using DatabaseFile file_path attribute
        self.start_session()
        self.table_class.metadata.create_all(self.engine)
        

    def add_item(self, **kwargs):
        """
        Adds a new item to the database. unpack a dictionary if attributes using "**" operator

        Args:
            **kwargs: Keyword arguments representing the attributes of the item to be added.
        """
        # TODO: see what happens in the database when not enough columns are given and do something to make it look nice
        # Check to make sure the dictionary keys match the database table columns
        if self._dict_compatible(kwargs):

            # Create a new instance of the database object class with the provided attributes
            new_item = self.table_class(**kwargs)

            try:
                # Add the new item to the session and commit the changes to the database
                self.session.add(new_item)
                self.session.flush() # Detects if the item already exists in the database

            except sqlalchemy.exc.IntegrityError as e:
                # Handle the IntegrityError if the item already exists in the database
                self.session.rollback() # Rollback the session to avoid leaving it in an inconsistent state
                logger.exception(f"Item already exists in database.", extra={
                                                                        LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                        LoggingExtras.ATTRIBUTES: kwargs
                                                                    })
                raise e
            
            finally:
                self.session.commit() # Commit the changes to the database
                logger.info(f"Item added to database.", extra={
                                                            LoggingExtras.TABLE_CLASS: self.table_class, 
                                                            LoggingExtras.ATTRIBUTES: kwargs
                                                        })
    

    def add_multiple_items(self, entries: List[dict[str, Any]]):
        """
        Adds a new item to the database. unpack a dictionary if attributes using "**" operator

        Args:
            **kwargs: Keyword arguments representing the attributes of the item to be added.
        """

        # Create a new instance of the database object class with the provided attributes
        for entry in entries:
            self.add_item(**entry)

        # Commit the changes to the database
        self.session.commit()


    def append_dataframe(self, df):
        """
        Appends a pandas DataFrame to the database table.

        Args:
            df (pd.DataFrame): The DataFrame to be appended to the database table.
        """

        # Check to make sure the dataframe columns match the database table columns
        if self._df_compatible(df):

            # Append the DataFrame to the database table using the SQLAlchemy engine
            df.to_sql(self.table_name, self.engine, if_exists="append", index=False)
            try:
                # Add the new item to the session and commit the changes to the database
                self.session.flush() # Detects if the item already exists in the database

            except sqlalchemy.exc.IntegrityError as e:
                # Handle the IntegrityError if the item already exists in the database
                self.session.rollback() # Rollback the session to avoid leaving it in an inconsistent state
                logger.exception(f"Dubplicates detected in : {self.table_name}.", extra={
                                                                                    LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                    LoggingExtras.COLUMNS: df.columns.tolist()
                                                                                })
                raise e
            
            finally:
                self.session.commit() # Commit the changes to the database
                logger.info(f"DataFrame appended to database: {self.table_name}.", extra={
                                                                                    LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                    LoggingExtras.COLUMNS: df.columns.tolist()
                                                                                })        


    def fetch_all_items(self) -> List[BaseTable] | None:
        """
        Fetches all items from the database table
        
        Returns:
            list[BaseTable] | None: A list of all BaseTable items in the database table or None if table is empty.
        """
        logger.debug(f"Fetching all items from database.", extra={LoggingExtras.TABLE_CLASS: self.table_class})

        result = self.session.query(self.table_class).all()
        if result != []:
            logger.debug(f"All items retrieved from database: {self.table_name}.", extra={LoggingExtras.TABLE_CLASS: self.table_class})
            return self.session.query(self.table_class).all()
        else:
            logger.warning(f"No items found in database: {self.table_name}.", extra={LoggingExtras.TABLE_CLASS: self.table_class})
            return None
    

    def fetch_item_by_id(self, item_id) -> List[BaseTable] | None:
        """
        Fetches an item from the database based on its ID.
        Requires the table has "id" column with unique values.
        
        Args:
            item_id (int): The ID of the item to be fetched.

        Returns:
            list[BaseTable] | None: A BaseTable item with matching id in the database table or None if table is empty.
        """

        # Locate the item in the database using its ID
        item = self.session.query(self.table_class).filter_by(id=item_id).first()

        # If the item exists, return it; otherwise, return None
        if item:
            logger.debug(f"Item found in database by ID: {item_id}.", extra={
                                                                        LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                        LoggingExtras.ITEM_ID: item_id
                                                                        })
            return item
        else:
            logger.warning(f"Item not found in database by ID: {item_id}.", extra={
                                                                            LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                            LoggingExtras.ITEM_ID: item_id
                                                                        })
            return None
    

    def fetch_items_by_attribute(self,**kwargs) -> List[BaseTable] | None:
        """
        Fetches items from the database based on specified attributes.
        Only supports equals and logic, no complex queries yet.
        
        Args:
            **kwargs: Keyword arguments representing the attributes to filter by. 
                      Keys should match column names and values should match the column types.

        Returns:
            list[BaseTable] | None: A list of all BaseTable items in the database table with matching attributes or None if table is empty.
        """

        # Create a query object to filter items based on the provided attributes
        query = self.session.query(self.table_class).filter_by(**kwargs)

        if query:
            # If the query returns results, return them as a list
            logger.debug("Items found in database by using attributes.", extra={
                                                                                LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                LoggingExtras.ATTRIBUTES: kwargs
                                                                            })
            return query.all()
        else:
            # If no results are found, return an empty list
            logger.warning("No items found in database by using attributes.", extra={
                                                                                LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                LoggingExtras.ATTRIBUTES: kwargs
                                                                            })
            return None


    def filter_items(self, filters: dict, use_or=False) -> List[BaseTable] | None:
        """
        Apply N filters with operators and return ORM objects.

        Args:
            filters (dict): A dictionary where keys are column names and values are tuples of (operator, value).
                            Supported operators: "==", "!=", ">", ">=", "<", "<=", "in", "like" (See _OPERATOR_MAP).
                            if value is no a tuple, equality is assumed.
            use_or (bool): Whether to combine filters with OR logic instead of AND. Default is False.
        
        Returns:
            list[BaseTable] | None: A list of all BaseTable items in the database table or None if table is empty.
        """
        logger.debug(f"Applying filters to database.", extra={LoggingExtras.TABLE_CLASS: self.table_class, LoggingExtras.FILTERS: filters})

        clauses = []
        query = self.session.query(self.table_class)

        for column_name, spec in filters.items():

            # Validate column name
            if not hasattr(self.table_class, column_name):
                logger.error(f"Invalid column in filters: {column_name}.", extra={
                                                            LoggingExtras.TABLE_CLASS: self.table_class, 
                                                            LoggingExtras.FILTERS: filters, 
                                                            LoggingExtras.COLUMNS: column_name
                                                            })
                raise AttributeError(f"Invalid column: {column_name}")

            # Loop over filters and build conditions
            column = getattr(self.table_class, column_name)

            if isinstance(spec, tuple):
                # If the spec is a tuple, unpack the operator and value.
                op, value = spec
            else:
                # If not, assume operator is equals.
                op, value = "==", spec

            try:
                # Create condition using the _OPERATOR_MAP
                condition = self._OPERATOR_MAP[op](column, value)
            except KeyError:
                logger.exception(f"Unsupported operator in filters: {op}.", extra={
                                                                    LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                    LoggingExtras.FILTERS: filters, 
                                                                    "operator": op
                                                                })
                raise ValueError(f"Unsupported operator: {op}")

            clauses.append(condition)
        
        if use_or: # Combine clauses with OR logic if use_or
            query = query.filter(sqlalchemy.or_(*clauses))

        else: # Combine clauses with AND logic
            query = query.filter(sqlalchemy.and_(*clauses))

        logger.debug("Filters successfully applied to database with filters", extra={
                                                                                    LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                    LoggingExtras.FILTERS: filters
                                                                                })
        result = query.all() 
        if result != []:
            return result
        else:
            logger.warning("No items found in database after applying filters.", extra={
                                                                                    LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                    LoggingExtras.FILTERS: filters
                                                                                })
            return  None

    
    def to_dataframe(self):
        """
        Converts the database table to a pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing all items in the database table.
        """

        # Fetch all items from the database and convert them to a DataFrame
        logger.debug("Converting database table to DataFrame.", extra={LoggingExtras.TABLE_CLASS: self.table_class})
        return pd.read_sql(self.session.query(self.table_class).statement, self.session.bind)


    def convert_orm_list_to_dataframe(self, orm_list: List[BaseTable]) -> pd.DataFrame:
        """
        Converts a list of ORM objects to a pandas DataFrame.

        Args:
            orm_list (List[BaseTable]): A list of ORM objects to be converted.

        Returns:
            pd.DataFrame: A DataFrame containing the data from the ORM objects.
        """

        # Convert the list of ORM objects to a DataFrame
        return orm_list_to_dataframe(orm_list)
    

    def update_item(self, item_id, **kwargs):
        """
        Updates an item in the database based on its ID.

        Args:
            item_id (int): The ID of the item to be updated.
            **kwargs: Keyword arguments representing the attributes to be updated.
        """
        logger.debug("Updating item in database.", extra={
                                                    LoggingExtras.TABLE_CLASS: self.table_class, 
                                                    LoggingExtras.ATTRIBUTES: kwargs
                                                })
        ## Check to make sure the dictionary keys match the database table columns
        if self._dict_columns_match(kwargs):
            
            # Locate the item in the database using its ID
            item = self.session.query(self.table_class).filter_by(id=item_id).first()

            # If the item exists, update its attributes and commit the changes to the database
            if item:
                # Unpack the keyword arguments and update the item"s attributes
                for key, value in kwargs.items():
                    if hasattr(item, key): # Check if the attribute exists in the item
                        setattr(item, key, value)

        try:
            self.session.flush() # Detects if the item already exists in the database

        except sqlalchemy.exc.IntegrityError as e:
            # Handle the IntegrityError if the item already exists in the database
            self.session.rollback() # Rollback the session to avoid leaving it in an inconsistent state
            logger.exception("Unable to update item, value already exists in database.", extra={
                                                                                            LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                            LoggingExtras.ATTRIBUTES: kwargs
                                                                                        })
            raise e
        
        finally:
            self.session.commit() # Commit the changes to the database
            logger.info(f"Item updated in database with ID {item_id}.", extra={LoggingExtras.TABLE_CLASS: self.table_class, LoggingExtras.ATTRIBUTES: kwargs})


    def delete_item(self, item_id):
        """
        Deletes an item from the database based on its ID.
        
        Args:
            item_id (int): The ID of the item to be deleted.
        """

        # Locate the item in the database using its ID
        item = self.session.query(self.table_class).filter_by(id=item_id).first()

        # If the item exists, delete it from the session and commit the changes to the database
        if item:
            self.session.delete(item)
            self.session.commit()
            logger.info(f"Item deleted from database with ID: {item_id}.", extra={
                                                                            LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                            LoggingExtras.ITEM_ID: item_id
                                                                        })
        else:
            logger.warning(f"Item not found in database with ID: {item_id}.", extra={
                                                                            LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                            LoggingExtras.ITEM_ID: item_id
                                                                        })

    
    def delete_items_by_attribute(self, **kwargs):
        """
        Deletes items from the database based on specified attributes.
        
        Args:
            **kwargs: Keyword arguments representing the attributes to filter by. 
                      Keys should match column names and values should match the column types.
        """
        logger.debug("Deleting items from database with given attributes", extra={
                                                                            LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                            LoggingExtras.ATTRIBUTES: kwargs
                                                                        })

        # Create a query object to filter items based on the provided attributes
        query = self.session.query(self.table_class).filter_by(**kwargs)

        # If the query returns results, delete them from the session and commit the changes to the database
        if query:
            for item in query.all():
                self.session.delete(item)
            self.session.commit()
            logger.info("Items deleted from database with given attributes.", extra={
                                                                                LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                LoggingExtras.ATTRIBUTES: kwargs
                                                                            })

        else:
            logger.warning("No items found in database with given attributes.", extra={
                                                                                LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                LoggingExtras.ATTRIBUTES: kwargs
                                                                            })


    def delete_items_by_filter(self, filters: dict, use_or=False):
        """
        Delete items from the database based on specified filters.

        Args:
            filters (dict): A dictionary where keys are column names and values are tuples of (operator, value).
                            Supported operators: "==", "!=", ">", ">=", "<", "<=", "in", "like" (See _OPERATOR_MAP).
            use_or (bool): Whether to combine filters with OR logic instead of AND. Default is False.
        """

        logger.debug("Deleting items from database using filters.", extra={
                                                                    LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                    LoggingExtras.FILTERS: filters, 
                                                                    LoggingExtras.USE_OR: use_or
                                                                })

        # get items to delete using the filter_items method
        items_to_delete = self.filter_items(filters, use_or=use_or)

        if items_to_delete is not None:
            for item in items_to_delete:
                self.session.delete(item)
            self.session.commit()
            logger.info("Items deleted from database using filters.", extra={
                                                                        LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                        LoggingExtras.FILTERS: filters, 
                                                                        LoggingExtras.USE_OR: use_or
                                                                    })
        
        else:
            logger.warning("No items found in database given with filters.", extra={
                                                                                LoggingExtras.TABLE_CLASS: self.table_class, 
                                                                                LoggingExtras.FILTERS: filters, 
                                                                                LoggingExtras.USE_OR: use_or
                                                                            })


    def clear_table(self):
        """
        Deletes all items from the database table.
        """

        # Delete all items from the database table
        num_deleted = self.session.query(self.table_class).delete()
        self.session.commit()
        logger.info(f"All items deleted from database table, total items deleted: {num_deleted}", extra={
                                                                                                    LoggingExtras.TABLE_CLASS: self.table_class
                                                                                                })


    def start_session(self):
        """Starts a new database session."""

        # Create a new session using the engine connection
        self.engine = create_engine_conn(self.file.file_path)
        self.session = create_session(self.engine)
        logger.info(f"DatabaseManager session started with table: {self.table_name}", extra={
                                                                                                        LoggingExtras.TABLE_CLASS: self.table_class,
                                                                                                        LoggingExtras.FILE_PATH: self.file.name
                                                                                                    })


    def end_session(self):
        """Ends the database session and closes the connection."""

        # Close the session and dispose of the engine connection
        self.session.close()
        self.engine.dispose()
        logger.info(f"DatabaseManager session ended with table: {self.table_name}", extra={
                                                                                                LoggingExtras.TABLE_CLASS: self.table_class,
                                                                                                LoggingExtras.FILE_PATH: self.file.name
                                                                                            })
    

    def _df_columns_match(self, df: pd.DataFrame) -> bool:
        """
        Checks if the columns of the input data match the columns of the database table.

        Args:
            database_input (pd.DataFrame): The input data to be checked.

        Returns:
            bool: True if the columns match, False otherwise.
        """

        # Check if the columns of the input data match the columns of the database table
        columns_match = set(df.columns).issubset(set(self.table_class.get_column_names()))

        if columns_match:
            logger.debug(f"DataFrame columns match database table columns.", extra={LoggingExtras.COLUMNS: df.columns.tolist()})
            return columns_match
        else:
            # Raise ValueError if they do not match
            logger.error(f"DataFrame columns do not match database table columns.", extra={LoggingExtras.COLUMNS: df.columns.tolist()})
            raise ValueError(f"DataFrame columns do not match database table columns: {df.columns.tolist()}")
    

    def _df_types_match(self, df: pd.DataFrame) -> bool:
        """
        Checks if the data types of the input DataFrame match the data types of the database table.

        Args:
            df (pd.DataFrame): The input DataFrame to be checked.
        
        Returns:
            bool: True if the data types match, False otherwise.
        """
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
            logger.debug(f"DataFrame types match database table types: {sql_datatypes}")
            return types_match
        else:
            # Raise ValueError if they do not match
            logger.error(f"DataFrame types do not match database table types: {sql_datatypes}")
            raise TypeError(f"DataFrame types do not match database table types: {sql_datatypes}")
    

    def _df_compatible(self, df: pd.DataFrame) -> bool:
        """
        Checks if the input DataFrame is compatible with the database table.

        Args:
            df (pd.DataFrame): The input DataFrame to be checked.

        Returns:
            bool: True if the DataFrame is compatible, False otherwise.
        """

        # Check if the columns and data types of the DataFrame match the database table
        return self._df_columns_match(df) and self._df_types_match(df)


    def _dict_columns_match(self, data: dict) -> bool:
        """
        Checks if the keys of the input dictionary match the columns of the database table.

        Args:
            data (dict): The input dictionary to be checked.

        Returns:
            bool: True if the keys match, False otherwise.
        """

        # Check if the keys of the input dictionary match the columns of the database table
        columns_match = set(data.keys()).issubset(set(self.table_class.get_column_names()))

        if columns_match:
            logger.debug(f"Dictionary columns match database table columns: {data.keys()}")
            return columns_match
        else:
            # Raise ValueError if they do not match
            logger.error(f"Dictionary columns do not match database table columns: {data.keys()}")
            raise ValueError(f"Dictionary columns do not match database table columns: {data.keys()}")


    def _dict_types_match(self, data: dict) -> bool:
        """
        Checks if the data types of the input DataFrame match the data types of the database table.

        Args:
            data: The input dict to be checked.
        
        Returns:
            bool: True if the data types match, False otherwise.
        """
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
            logger.debug(f"Dictionary types match database table types: {sql_datatypes}")
            return types_match
        else:
            # Raise ValueError if they do not match
            logger.error(f"ictionary types do not match database table types: {sql_datatypes}")
            raise TypeError(f"Dictionary types do not match database table types: {sql_datatypes}")
        

    def _dict_compatible(self, data: dict) -> bool:
        """
        Checks if the input dictionary is compatible with the database table.

        Args:
            data (dict): The input dictionary to be checked.

        Returns:
            bool: True if the dictionary is compatible, False otherwise.
        """

        # Check if the columns and data types of the DataFrame match the database table
        return self._dict_columns_match(data) and self._dict_types_match(data)
    

    @property
    def _OPERATOR_MAP(self) -> dict:
        return {
            "==": lambda c, v: c == v,
            "!=": lambda c, v: c != v,
            ">":  lambda c, v: c > v,
            ">=": lambda c, v: c >= v,
            "<":  lambda c, v: c < v,
            "<=": lambda c, v: c <= v,
            "in": lambda c, v: c.in_(v),
            "like": lambda c, v: c.like(v)
            }
    