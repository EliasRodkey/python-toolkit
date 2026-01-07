# local_db_handler

this package is a modular python package that allows for easy
creation, reading, editing, and deleting local database files

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Usage/Examples

**Install Package**
Ensure you have access to the github repository
Run the command:
    pip install git+<https://github.com/EliasRodkey/local_db.git>

### Import Package

```python
From local_db_handler import DatabaseFile, DatabaseManager, BaseTable
```

### Set Up Table Object

Use the BaseTable class to create a table object that will be connected to using the DatabaseManager

```python
class TableName(BaseTable):
    '''A table object'''
    __tablename__ = 'table_name'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    age = Column(Integer)
    email = Column(String(100), unique=True)
```

The attributes here represent column names in the table, additional funcionality can be added to avoid duplicate entries, for example:

```python
email = Column(String(100), unique=True)
```

This forces all emails to be unique in the table.
Another option is to add a special hash row that would be unique to each entry:

```python
    import hashlib

def generate_hash(row):
    # Concatenate values of all relevant columns
    data = f"{row['col1']}_{row['col2']}_{row['col3']}"
    return hashlib.sha256(data.encode()).hexdigest()

df['unique_id'] = df.apply(generate_hash, axis=1)
```

Additionally the \_\_tableargs\_\_ can be updated to make a custom unique filter based on multiple columns to the class attributes:

```python
__table_args__ = (
    UniqueConstraint('column1', 'column2', name='unique_combo'),  # Combination must be unique
)
```

### Creating the DataFile

The DatabaseFile object represents the actual file of the database and is required to initialize a DatabaseManager object.

```python
file = DatabaseFile(db_name, directory='data/dbs')

db_name: valid .db filename
directory: relative path to database directory (default data//dbs)
```

DatabaseFile funcitons:

```python
file.create() # Creates a db file in the directory location
file.move(target_directory) # Moves the db file to a new directory
file.exists() # Returns boolean, if the file exists
file.delete() # Deletes the actual db file
```

### Create DatabaseManager

The DatabaseManager takes a file and table as arguments and allows for common database operations on that table

```python
manager = DatabaseManager(table_class: BaseTable, databasefile: DatabaseFile)
```

The DatabaseFile functions can be accessed through the DatabaseManager.file attribute
Basic database funcitons:

```python
manager.add_item(entry: dictionary with columns matching the db table class)
manager.add_multiple_items(entries: list of entries)
manager.append_dataframe(df: pandas DataFrame with columns that match the db table class)

manager.fetch_all(as_dataframe=True) -> returns all table class instances in the table
manager.fetch_item_by_id(id: int, as_dataframe=True) -> returns an individual table class instance with data
manager.fetch_items_by_attribute(**kwargs, as_dataframe=True) -> allows filtering of table by kwargs
manager.filter_items(filters: dict, use_or=False, as_dataframe=True) -> allows filtering of database table and reading of filtered items
manager.to_dataframe() -> Returns the entire database as a pandas DataFrame

manager.update_item(item_id: int, **kwargs) -> updates values kwargs of an item with a given ID
manager.delete_item(item_id: int) -> Deletes an item with the given item id
manager.delete_items_by_attribute(**kwargs) -> Deletes items in a database where column values match kwargs.
manager.delete_items_by_filter(filters: dict, use_or=False) -> Deletes items in a database where filters apply.
manager.clear_table() -> Deletes all items in the database table.

manager.start_session() -> initiates when instance initialized
manager.end_session() -> should be called before exiting program
```
