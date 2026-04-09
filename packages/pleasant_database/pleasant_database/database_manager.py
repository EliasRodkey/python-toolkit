#!python3
"""
pleasant_database.database_manager.py

This module contains a database object class.
logger in this module used LoggingExtras.TABLE_NAME to refer to the current table class name in json logging.

Classes:
    - DatabaseManager: a class object which allows for the following actions to be performed:
        - Creation
        - Reading
        - Editing
        - Updating
        - Deletion

Filter API:
    filter_items and delete_items_by_filter accept a ``filters`` dict where each value can be:
        - A bare value (equality assumed): ``{"name": "coffee"}``
        - A (operator, value) tuple: ``{"age": (">", 5)}``
        - A list of (operator, value) tuples for multiple constraints on one column:
          ``{"timestamp": [(">=", start), ("<=", end)]}``

    Supported operators: "==", "!=", ">", ">=", "<", "<=", "in", "like", "ilike", "between"
    The "between" operator requires a 2-element (lower, upper) sequence as its value:
        ``{"age": ("between", (18, 65))}``
"""
# Standard library imports
from datetime import datetime, date
from typing import List, Any

# Third-Party library imports
import pandas as pd
import sqlalchemy

# local imports
from pleasant_database.database_connections import create_engine_conn, create_session
from pleasant_database.base_table import BaseTable, DatabaseIntegrityError, ItemNotFoundError
from pleasant_database.database_file import DatabaseFile
from pleasant_database.utils import LoggingExtras, map_dtype_list_to_sql, orm_list_to_dataframe


# Initialize module logger
import logging
logger = logging.getLogger(__name__)



class DatabaseManager():
    """
    Generic Database manager wrapper class that allows for simple database operations to be performed on a local database file.
    Supports use as a context manager (with statement) for automatic session cleanup.

    Functions:
        - add_item: Adds a new item to the database.
        - add_multiple_items: Adds multiple new items to the database.
        - append_dataframe: Appends a pandas DataFrame to the database table.
        - fetch_all_items: Fetches all items from the database table.
        - fetch_item_by_id: Fetches an item by ID; raises ItemNotFoundError if missing.
        - fetch_items_by_attribute: Fetches items from the database based on specified attributes.
        - filter_items: Apply N filters with operators and return ORM objects.
        - query: Flexible DataFrame-returning query with optional column projection, filtering, sorting, pagination, and substring search.
        - convert_orm_list_to_dataframe: Converts a list of ORM objects to a pandas DataFrame.
        - to_dataframe: Converts the database table to a pandas DataFrame.
        - upsert: Inserts a new item or updates an existing one based on a match dict.
        - count_items: Returns the count of items matching given attributes.
        - exists: Returns True if any item matching given attributes exists.
        - update_item: Updates an item in the database based on its ID.
        - delete_item: Deletes an item from the database based on its ID.
        - delete_items_by_attribute: Deletes items matching given attributes.
        - delete_items_by_filter: Deletes items matching N filter conditions.
        - clear_table: Deletes all items from the table.
        - start_session: Starts a new database session.
        - end_session: Ends the database session and closes the connection.

    Private helpers:
        - _build_filter_clauses: Converts a filters dict into a list of SQLAlchemy conditions.
        - _build_single_clause: Builds one SQLAlchemy condition from a column and a spec.
        - _validate_columns: Validates a list of column name strings against the table schema.
        - _normalise_order_by: Normalises the order_by parameter to a list of (column, direction) tuples.
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
                logger.info(f"Item added to database.", extra={LoggingExtras.TABLE_NAME: self.table_name})

            except sqlalchemy.exc.IntegrityError as e:
                # Handle the IntegrityError if the item already exists in the database
                self.session.rollback() # Rollback the session to avoid leaving it in an inconsistent state
                logger.error(f"Database integrity error on add.", extra={LoggingExtras.TABLE_NAME: self.table_name})
                raise DatabaseIntegrityError(e, self.table_class)
            
            finally:
                self.session.commit() # Commit the changes to the database
    

    def add_multiple_items(self, entries: List[dict[str, Any]]):
        """
        Adds a new item to the database. unpack a dictionary if attributes using "**" operator

        Args:
            **kwargs: Keyword arguments representing the attributes of the item to be added.
        """

        for entry in entries:
            self.add_item(**entry)


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
                logger.info(f"DataFrame appended to database: {self.table_name}.", extra={
                                                                                    LoggingExtras.TABLE_NAME: self.table_name, 
                                                                                    LoggingExtras.COLUMNS: df.columns.tolist()
                                                                                })  

            except sqlalchemy.exc.IntegrityError as e:
                # Handle the IntegrityError if the item already exists in the database
                self.session.rollback() # Rollback the session to avoid leaving it in an inconsistent state
                logger.error(f"Database integrity error on DataFrame append.", extra={
                                                                                    LoggingExtras.TABLE_NAME: self.table_name,
                                                                                    LoggingExtras.COLUMNS: df.columns.tolist()
                                                                                })
                raise DatabaseIntegrityError(e, self.table_class)
            
            finally:
                self.session.commit() # Commit the changes to the database      


    def fetch_all_items(self) -> List[BaseTable]:
        """
        Fetches all items from the database table

        Returns:
            list[BaseTable]: A list of all BaseTable items in the database table, or an empty list if the table is empty.
        """
        logger.debug(f"Fetching all items from database.", extra={LoggingExtras.TABLE_NAME: self.table_name})

        result = self.session.query(self.table_class).all()
        if result:
            logger.debug(f"All items retrieved from database: {self.table_name}.", extra={LoggingExtras.TABLE_NAME: self.table_name})
        else:
            logger.warning(f"No items found in database: {self.table_name}.", extra={LoggingExtras.TABLE_NAME: self.table_name})
        return result
    

    def fetch_item_by_id(self, item_id) -> BaseTable:
        """
        Fetches an item from the database based on its ID.
        Requires the table has "id" column with unique values.

        Args:
            item_id (int): The ID of the item to be fetched.

        Returns:
            BaseTable: The item with the matching ID.

        Raises:
            ItemNotFoundError: If no item with the given ID exists in the table.
        """

        item = self.session.query(self.table_class).filter_by(id=item_id).first()

        if item:
            logger.debug(f"Item found in database by ID: {item_id}.", extra={
                                                                        LoggingExtras.TABLE_NAME: self.table_name,
                                                                        LoggingExtras.ITEM_ID: item_id
                                                                    })
            return item

        logger.warning(f"Item not found in database by ID: {item_id}.", extra={
                                                                        LoggingExtras.TABLE_NAME: self.table_name,
                                                                        LoggingExtras.ITEM_ID: item_id
                                                                    })
        raise ItemNotFoundError(item_id, self.table_class)
    

    def fetch_items_by_attribute(self,**kwargs) -> List[BaseTable]:
        """
        Fetches items from the database based on specified attributes.
        Only supports equals and logic, no complex queries yet.

        Args:
            **kwargs: Keyword arguments representing the attributes to filter by.
                      Keys should match column names and values should match the column types.

        Returns:
            list[BaseTable]: A list of all BaseTable items with matching attributes, or an empty list if none found.
        """

        # Create a query object to filter items based on the provided attributes
        result = self.session.query(self.table_class).filter_by(**kwargs).all()

        if result:
            logger.debug("Items found in database by using attributes.", extra={LoggingExtras.TABLE_NAME: self.table_name})
        else:
            logger.warning("No items found in database by using attributes.", extra={LoggingExtras.TABLE_NAME: self.table_name})
        return result


    def filter_items(self, filters: dict, use_or=False) -> List[BaseTable]:
        """
        Apply N filters with operators and return ORM objects.

        Args:
            filters (dict): A dictionary where keys are column names and values can be:
                            - A bare value (equality assumed): ``{"name": "coffee"}``
                            - A (operator, value) tuple: ``{"age": (">", 5)}``
                            - A list of (operator, value) tuples for multiple constraints on one column:
                              ``{"timestamp": [(">=", start), ("<=", end)]}``
                            Supported operators: "==", "!=", ">", ">=", "<", "<=", "in", "like", "ilike", "between"
                            (See _OPERATOR_MAP). The "between" operator requires a 2-element (lower, upper) sequence.
            use_or (bool): Whether to combine filters with OR logic instead of AND. Default is False.

        Returns:
            list[BaseTable]: A list of matching BaseTable items, or an empty list if none found.
        """
        logger.debug(f"Applying filters to database.", extra={LoggingExtras.TABLE_NAME: self.table_name})

        clauses = self._build_filter_clauses(filters)
        query = self.session.query(self.table_class)

        if use_or:
            query = query.filter(sqlalchemy.or_(*clauses))
        else:
            query = query.filter(sqlalchemy.and_(*clauses))

        logger.debug("Filters successfully applied to database.", extra={LoggingExtras.TABLE_NAME: self.table_name})
        result = query.all()
        if not result:
            logger.warning("No items found in database after applying filters.", extra={LoggingExtras.TABLE_NAME: self.table_name})
        return result

    
    def to_dataframe(self):
        """
        Converts the database table to a pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing all items in the database table.
        """

        # Fetch all items from the database and convert them to a DataFrame
        logger.debug("Converting database table to DataFrame.", extra={LoggingExtras.TABLE_NAME: self.table_name})
        return pd.read_sql(self.session.query(self.table_class).statement, self.session.bind)


    def query(
        self,
        columns: list[str] | None = None,
        filters: dict | None = None,
        order_by: str | tuple | list | None = None,
        ascending: bool = True,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
        search_columns: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        Flexible DataFrame-returning query with optional column projection, filtering, sorting, and pagination.

        Args:
            columns (list[str] | None): Column names to return. None returns all columns.
            filters (dict | None): Filter dict using the same format as filter_items(). None applies no filter.
            order_by: Column(s) to sort by. Accepted forms:
                - str: ``"age"`` — sorts ascending by default (use ``ascending`` to flip)
                - tuple: ``("age", "desc")`` — single column with explicit direction
                - list of tuples: ``[("age", "desc"), ("name", "asc")]`` — multi-column sort
                - None or []: no sorting applied
            ascending (bool): Sort direction when order_by is a bare string. Default True.
            limit (int | None): Maximum number of rows to return. None returns all.
            offset (int | None): Number of rows to skip before returning results. None skips none.
            search (str | None): Substring to search for across string columns (case-insensitive).
                A row is returned if the term appears in *any* of the searched columns.
                Automatically wrapped as ``%term%``. Combined with ``filters`` using AND logic.
                None disables search entirely.
            search_columns (list[str] | None): Columns to search when ``search`` is set.
                Defaults to all ``str``-typed columns on the table.
                All specified columns must exist and be string-typed, otherwise ValueError is raised.

        Returns:
            pd.DataFrame: Query results. Empty DataFrame if no rows match.

        Raises:
            ValueError: If columns is an empty list, an invalid column name is given in columns,
                        order_by, or search_columns, or if search_columns contains a non-string column,
                        or an invalid/malformed order_by direction/tuple is given.
            AttributeError: If a filter column name does not exist on the table.
        """
        logger.debug("Executing query.", extra={LoggingExtras.TABLE_NAME: self.table_name})

        # Guard: empty columns list is ambiguous — reject it early
        if columns is not None and len(columns) == 0:
            raise ValueError("columns list must not be empty")

        # Normalise order_by to list[tuple[str, str]]
        normalised_order_by = self._normalise_order_by(order_by, ascending)

        # Build base query
        if columns is None:
            q = self.session.query(self.table_class)
            selecting_columns = False
        else:
            self._validate_columns(columns, "columns")
            col_attrs = [getattr(self.table_class, col) for col in columns]
            q = self.session.query(*col_attrs)
            selecting_columns = True

        # Apply filters
        if filters is not None:
            clauses = self._build_filter_clauses(filters)
            q = q.filter(sqlalchemy.and_(*clauses))

        # Apply search (case-insensitive partial match across string columns)
        if search is not None:
            col_types = self.table_class.get_column_python_types()
            if search_columns is None:
                resolved = [col for col, typ in col_types.items() if typ == str]
            else:
                self._validate_columns(search_columns, "search_columns")
                non_str = [col for col in search_columns if col_types.get(col) != str]
                if non_str:
                    raise ValueError(
                        f"search_columns must only contain string-typed columns. Non-string: {non_str}"
                    )
                resolved = search_columns
            ilike_clauses = [getattr(self.table_class, col).ilike(f"%{search}%") for col in resolved]
            q = q.filter(sqlalchemy.or_(*ilike_clauses))

        # Apply sorting
        for col_name, direction in normalised_order_by:
            col_attr = getattr(self.table_class, col_name)
            q = q.order_by(col_attr.asc() if direction == "asc" else col_attr.desc())

        # Apply pagination (offset before limit)
        if offset is not None:
            q = q.offset(offset)
        if limit is not None:
            q = q.limit(limit)

        rows = q.all()

        if not rows:
            logger.warning("query() returned no results.", extra={LoggingExtras.TABLE_NAME: self.table_name})

        if selecting_columns:
            return pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)
        else:
            return orm_list_to_dataframe(rows)

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
        logger.debug(f"Updating item in database {self.table_name} id: {item_id}.", extra={
                                            LoggingExtras.TABLE_NAME: self.table_name, 
                                            LoggingExtras.ITEM_ID: item_id,
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
            else:
                raise ItemNotFoundError(item_id, self.table_class)

        try:
            self.session.flush() # Detects if the item already exists in the database
            logger.info(f"Item updated in database with ID {item_id}.", extra={LoggingExtras.TABLE_NAME: self.table_name, LoggingExtras.ITEM_ID: item_id})

        except sqlalchemy.exc.IntegrityError as e:
            # Handle the IntegrityError if the item already exists in the database
            self.session.rollback() # Rollback the session to avoid leaving it in an inconsistent state
            logger.error("Database integrity error on update.", extra={LoggingExtras.TABLE_NAME: self.table_name, LoggingExtras.ITEM_ID: item_id})
            raise DatabaseIntegrityError(e, self.table_class)
        
        finally:
            self.session.commit() # Commit the changes to the database
            


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
                                                                            LoggingExtras.TABLE_NAME: self.table_name,
                                                                            LoggingExtras.ITEM_ID: item_id
                                                                        })
        else:
            logger.warning(f"Item not found in database with ID: {item_id}.", extra={
                                                                            LoggingExtras.TABLE_NAME: self.table_name,
                                                                            LoggingExtras.ITEM_ID: item_id
                                                                        })
            raise ItemNotFoundError(item_id, self.table_class)

    
    def delete_items_by_attribute(self, **kwargs):
        """
        Deletes items from the database based on specified attributes.
        
        Args:
            **kwargs: Keyword arguments representing the attributes to filter by. 
                      Keys should match column names and values should match the column types.
        """
        logger.debug("Deleting items from database with given attributes", extra={LoggingExtras.TABLE_NAME: self.table_name})

        num_deleted = self.session.query(self.table_class).filter_by(**kwargs).delete(synchronize_session="fetch")
        self.session.commit()

        if num_deleted:
            logger.info("Items deleted from database with given attributes.", extra={LoggingExtras.TABLE_NAME: self.table_name})
        else:
            logger.warning("No items found in database with given attributes.", extra={LoggingExtras.TABLE_NAME: self.table_name})


    def delete_items_by_filter(self, filters: dict, use_or=False):
        """
        Delete items from the database based on specified filters.

        Args:
            filters (dict): A dictionary where keys are column names and values are tuples of (operator, value).
                            Supported operators: "==", "!=", ">", ">=", "<", "<=", "in", "like", "ilike" (See _OPERATOR_MAP).
            use_or (bool): Whether to combine filters with OR logic instead of AND. Default is False.
        """

        logger.debug("Deleting items from database using filters.", extra={
                                                                    LoggingExtras.TABLE_NAME: self.table_name,
                                                                    LoggingExtras.USE_OR: use_or
                                                                })

        clauses = self._build_filter_clauses(filters)
        query = self.session.query(self.table_class)

        if use_or:
            query = query.filter(sqlalchemy.or_(*clauses))
        else:
            query = query.filter(sqlalchemy.and_(*clauses))

        num_deleted = query.delete(synchronize_session="fetch")
        self.session.commit()

        if num_deleted:
            logger.info("Items deleted from database using filters.", extra={
                                                                        LoggingExtras.TABLE_NAME: self.table_name,
                                                                        LoggingExtras.USE_OR: use_or
                                                                    })
        else:
            logger.warning("No items found in database given with filters.", extra={
                                                                                LoggingExtras.TABLE_NAME: self.table_name,
                                                                                LoggingExtras.USE_OR: use_or
                                                                            })


    def clear_table(self):
        """
        Deletes all items from the database table.
        """

        # Delete all items from the database table
        num_deleted = self.session.query(self.table_class).delete()
        self.session.commit()
        logger.info(f"All items deleted from database table, total items deleted: {num_deleted}", extra={LoggingExtras.TABLE_NAME: self.table_name})


    def upsert(self, match_by: dict, **update_kwargs):
        """
        Updates an existing record if found, or inserts a new one if not.

        Args:
            match_by (dict): Attributes used to locate the existing record (equality match).
            **update_kwargs: Attributes to set on update, or to merge with match_by on insert.
        """
        existing = self.fetch_items_by_attribute(**match_by)
        if existing:
            item = existing[0]
            for key, value in update_kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            self.session.commit()
            logger.info("Item upserted (updated) in database.", extra={LoggingExtras.TABLE_NAME: self.table_name})
        else:
            self.add_item(**{**match_by, **update_kwargs})
            logger.info("Item upserted (inserted) in database.", extra={LoggingExtras.TABLE_NAME: self.table_name})


    def count_items(self, **kwargs) -> int:
        """
        Returns the count of items matching the given attributes.

        Args:
            **kwargs: Keyword arguments representing the attributes to filter by.
                      If empty, counts all items in the table.

        Returns:
            int: The number of matching items.
        """
        return self.session.query(self.table_class).filter_by(**kwargs).count()


    def exists(self, **kwargs) -> bool:
        """
        Returns True if at least one item matching the given attributes exists.

        Args:
            **kwargs: Keyword arguments representing the attributes to filter by.

        Returns:
            bool: True if a matching item exists, False otherwise.
        """
        return self.count_items(**kwargs) > 0


    def start_session(self):
        """Starts a new database session."""

        # Create a new session using the engine connection
        self.engine = create_engine_conn(self.file.file_path)
        self.session = create_session(self.engine)
        logger.info(f"DatabaseManager session started with table: {self.table_name}", extra={
                                                                                        LoggingExtras.TABLE_NAME: self.table_name,
                                                                                        LoggingExtras.FILE: self.file.name
                                                                                    })


    def end_session(self):
        """Ends the database session and closes the connection."""

        # Close the session and dispose of the engine connection
        self.session.close()
        self.engine.dispose()
        logger.info(f"DatabaseManager session ended with table: {self.table_name}", extra={
                                                                                    LoggingExtras.TABLE_NAME: self.table_name,
                                                                                    LoggingExtras.FILE: self.file.name
                                                                                })


    def __enter__(self):
        """Supports use as a context manager. Returns self."""
        return self


    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        """Automatically calls end_session() when exiting a with block."""
        self.end_session()
        return False
    

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
        table_datatypes_set = set(self.table_class.get_column_sqla_types().items())

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
        # Map the data types of the dict values to SQLAlchemy types.
        # Pass type(value) for date/datetime so map_dtype_to_sql can distinguish them
        # from plain strings, which pandas also represents as object dtype.
        sql_datatypes = map_dtype_list_to_sql([
            type(v) if isinstance(v, (datetime, date)) else pd.Series([v]).dtype
            for v in data.values()
        ])
        sql_datatypes_dict = {}
        for i, column in enumerate(data.keys()):
            sql_datatypes_dict[column] = sql_datatypes[i]

        # Get the data types of the database table columns
        table_datatypes_set = set(self.table_class.get_column_sqla_types().items())

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
    

    _OPERATOR_MAP = {
        "==":      lambda c, v: c == v,
        "!=":      lambda c, v: c != v,
        ">":       lambda c, v: c > v,
        ">=":      lambda c, v: c >= v,
        "<":       lambda c, v: c < v,
        "<=":      lambda c, v: c <= v,
        "in":      lambda c, v: c.in_(v),
        "like":    lambda c, v: c.like(v),
        "ilike":   lambda c, v: c.ilike(v),
        "between": lambda c, v: c.between(v[0], v[1]),
    }


    def _validate_columns(self, columns: list[str], context: str) -> None:
        """Raises ValueError if any name in columns is not a column on the table."""
        valid = set(self.table_class.get_column_names())
        for col in columns:
            if col not in valid:
                logger.error(
                    f"Invalid column '{col}' in {context}.",
                    extra={LoggingExtras.TABLE_NAME: self.table_name, LoggingExtras.COLUMNS: col},
                )
                raise ValueError(f"Invalid column '{col}' in {context}. Valid columns: {sorted(valid)}")


    def _normalise_order_by(self, order_by, ascending: bool) -> list[tuple[str, str]]:
        """
        Normalises the order_by parameter to a list of (column, direction) tuples.

        Raises:
            ValueError: If a tuple doesn't have exactly 2 elements, the direction is invalid,
                        or a column name doesn't exist on the table.
        """
        if order_by is None or order_by == []:
            return []

        # Wrap bare string and single tuple into a list for uniform processing
        if isinstance(order_by, str):
            order_by = [(order_by, "asc" if ascending else "desc")]
        elif isinstance(order_by, tuple):
            if len(order_by) != 2:
                raise ValueError(
                    f"order_by tuple must have exactly 2 elements (column, direction), got {len(order_by)}"
                )
            order_by = [order_by]

        result = []
        for item in order_by:
            if not isinstance(item, tuple) or len(item) != 2:
                raise ValueError(
                    f"Each order_by entry must be a 2-element tuple (column, direction), got: {item!r}"
                )
            col_name, direction = item
            direction = direction.lower()
            if direction not in ("asc", "desc"):
                raise ValueError(f"Invalid sort direction '{direction}'. Must be 'asc' or 'desc'.")
            result.append((col_name, direction))

        col_names = [col for col, _ in result]
        self._validate_columns(col_names, "order_by")
        return result


    def _build_single_clause(self, column, spec):
        """
        Builds a single SQLAlchemy filter condition from a column and spec.

        Args:
            column: The SQLAlchemy column object.
            spec: A tuple of (operator, value), or a bare value (equality assumed).
                  For the "between" operator, value must be a 2-element sequence (lower, upper).

        Returns:
            A SQLAlchemy filter condition.

        Raises:
            ValueError: If the operator is not in _OPERATOR_MAP, or if "between" is given
                        a value that is not a 2-element sequence.
        """
        op, value = spec if isinstance(spec, tuple) else ("==", spec)
        if op == "between":
            if not hasattr(value, "__len__") or len(value) != 2:
                logger.error(f"'between' operator requires a 2-element sequence, got: {value!r}.", extra={
                    LoggingExtras.TABLE_NAME: self.table_name
                })
                raise ValueError("'between' operator requires a 2-element (lower, upper) sequence")
        try:
            return self._OPERATOR_MAP[op](column, value)
        except KeyError:
            logger.exception(f"Unsupported operator in filters: {op}.", extra={
                LoggingExtras.TABLE_NAME: self.table_name,
                "operator": op
            })
            raise ValueError(f"Unsupported operator: {op}")


    def _build_filter_clauses(self, filters: dict) -> list:
        """
        Builds a list of SQLAlchemy filter conditions from a filters dict.

        Args:
            filters (dict): A dictionary where keys are column names and values are:
                            - A bare value (equality assumed), e.g. ``"coffee"``
                            - A tuple of (operator, value), e.g. ``(">", 5)``
                            - A list of (operator, value) tuples to apply multiple constraints
                              on the same column, e.g. ``[(">=", start), ("<=", end)]``

        Returns:
            list: SQLAlchemy filter conditions.

        Raises:
            AttributeError: If a column name does not exist on the table.
            ValueError: If an operator is not in _OPERATOR_MAP or "between" receives an invalid value.
        """
        clauses = []
        for column_name, spec in filters.items():

            if not hasattr(self.table_class, column_name):
                logger.error(f"Invalid column in filters: {column_name}.", extra={
                                                            LoggingExtras.TABLE_NAME: self.table_name,
                                                            LoggingExtras.COLUMNS: column_name
                                                        })
                raise AttributeError(f"Invalid column: {column_name}")

            column = getattr(self.table_class, column_name)
            if isinstance(spec, list):
                for subspec in spec:
                    clauses.append(self._build_single_clause(column, subspec))
            else:
                clauses.append(self._build_single_clause(column, spec))

        return clauses
    

    def __repr__(self):
        return f"{self.__class__.__name__}(table={self.table_name}, file={self.file.name})"