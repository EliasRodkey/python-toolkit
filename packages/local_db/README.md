# local_db_handler

this package is a modular python package that allows for easy
creation, reading, editing, and deleting local database files

## License

[MIT](https://choosealicense.com/licenses/mit/)

## Usage/Examples

1. **Install Package**
Ensure you have access to the github repository
Run the command:
    pip install git+https://github.com/EliasRodkey/local_db_handler.git


2. **Import Package**
    From local_db_handler import DatabaseFile, DatabaseManager, BaseTable

3. **Set Up Table Object**
Use the BaseTable class to create a table object that will be connected to using the DatabaseManager

    class TableName(BaseTable):
        '''A table object'''
        __tablename__ = 'table_name'
        id = Column(Integer, primary_key=True, autoincrement=True)
        name = Column(String(50), nullable=False)
        age = Column(Integer)
        email = Column(String(100), unique=True)

The attributes here represent column names in the table, additional funcionality can be added to avoid duplicate entries, for example:

    email = Column(String(100), unique=True)

This forces all emails to be unique in the table.
Another option is to add a special hash row that would be unique to each entry:

    import hashlib

    def generate_hash(row):
        # Concatenate values of all relevant columns
        data = f"{row['col1']}_{row['col2']}_{row['col3']}"
        return hashlib.sha256(data.encode()).hexdigest()

    df['unique_id'] = df.apply(generate_hash, axis=1)

Additionally the __tableargs__ can be updated to make a custom unique filter based on multiple columns to the class attributes:

    __table_args__ = (
        UniqueConstraint('column1', 'column2', name='unique_combo'),  # Combination must be unique
    )

4. **Creating the DataFile**
The DatabaseFile object represents the actual file of the database and is required to initialize a DatabaseManager object.

    file = DatabaseFile(db_name, directory='data\dbs')

    db_name: valid .db filename
    directory: relative path to database directory (default data\dbs)

DatabaseFile funcitons:

    file.create() # Creates a db file in the directory location
    file.move(target_directory) # Moves the db file to a new directory
    file.exists() # Returns boolean, if the file exists
    file.delete() # Deletes the actual db file

5. **Create DatabaseManager**
The DatabaseManager takes a file and table as arguments and allows for common database operations on that table

    manager = DatabaseManager(table_class: BaseTable, databasefile: DatabaseFile)

The DatabaseFile functions can be accessed through the DatabaseManager.file attribute
Basic database funcitons:

    manager.add_item(entry: dictionary with columns matching the db table class)
    manager.add_multiple_items(entries: list of entries)
    manager.append_dataframe(df: pandas DataFrame with columns that match the db table class)
    manager.fetch_all() -> returns all table class instances in the table
    manager.fetch_item_by_id(id: int) -> returns an individual table class instance with data
    manager.fetch_items_by_attribute(**kwargs) -> allows filtering of table by kwargs
    manager.