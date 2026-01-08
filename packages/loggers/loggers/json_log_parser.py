'''
loggers.json_log_parser.py

Class:
    JSONLogParser: Class that reads, filters, and interprets a JSON log file.
'''
from collections import Counter
from datetime import datetime
from enum import Enum
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Union, TypedDict, Any



class LogRecord(TypedDict, total=False):
    '''Expected log record json output (see JSONFormatter in loggers.logger_configs)'''
    timestamp: datetime
    level: str
    logger: str
    message: str
    module: str
    function: str
    line: str
    exception: str
    extras: dict[str, Any]



class ECoreFields(str, Enum):
    '''An Enum class that contains the core fields expected in the JSONLogParser'''
    TIMESTAMP = 'timestamp'
    LEVEL = 'level'
    LOGGER = 'logger'
    MESSAGE = 'message'
    MODULE = 'module'
    FUNCTION = 'function'
    LINE = 'line'
    EXCEPTION = 'exception'
    EXTRAS = 'extras'

    def __str__(self):
        return str(self.value)



class JSONLogParser():
    """
    Class that reads, filters, and interprets a JSON log file.

    Attributes:
        file_path (str): The path to the log file to examine.
    
    Methods:
        load: Loads the json log from the given path. Populates self.records and records metrics.
        filter_by_level(*levels: str): Allows filtering of the log based on the desired logging level.
        filter_by_time(start_date: datetime|None, end_date: datetime|None): Allows filtering of the log based on a given timeframe.
        get_extra(record: LogRecord, key: str, default): Allows extraction of a key within the extra dictionary if it exists.
        top_messages(n:int): Returns the top n messages and the number of times they occur
        level_counts: Returns the _level_counts Counter as a dictionary
        module_counts: Returns the _module_counts Counter as a dictionary
        func_counts: Returns the _func_counts Counter as a dictionary
        to_dataframe(List[LogRecord]|None): Converts either the entire self.records or a given list of records to a pandas dataframe.
    """
    CORE_FIELDS = [member.value for member in ECoreFields]


    def __init__(self, file_path: str) -> None:
        """
        Initializes an instance of LogParser.

        Args:
            file_path (str): The path to the log file to examine.
        """
        if not file_path.endswith('.json.log'):
            # If the file path isn't to a .log file raise an exception
            raise ValueError(f'Invalid .log file path supplied to {self.__class__.__name__}: {file_path}')
        
        self.file_path = Path(file_path)
        self.records: List[LogRecord] = []

        # Initialize counters for different logging metrics
        self._level_counts = Counter()
        self._module_counts = Counter()
        self._func_counts = Counter()


    def load(self) -> None:
        '''Loads the json log from the given path. Populates self.records and records metrics'''
        # Open the json log file and iterate over each line, loading json and adding records to the parser.
        with self.path.open() as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                raw = json.loads(line)
                record = self._normalize(raw)
                self.records.append(record)
                self._record_metrics(record)

    
    def filter_by_level(self, *levels: str) -> List[LogRecord]:
        '''
        Allows filtering of the log based on the desired logging level.

        Args:
            levels (str | List[str]): The desired levels to filter

        Returns:
            List[LogRecord]: list of LogRecord typed dicts matching the provided levels
        '''
        return [r for r in self.records if r.get(ECoreFields.LEVEL) in levels]
    

    def filter_by_time(self, start_date: datetime|None=None, end_date: datetime|None=None) -> List[LogRecord]:
        '''
        Allows filtering of the log based on a given timeframe.

        Args:
            start_date (datetime | None)
            end_date (datetime | None)

        Returns:
            List[LogRecord]: list of LogRecord typed dicts matching the provided levels
        '''
        def in_range(r: LogRecord) -> bool:
            ts = r.get(ECoreFields.TIMESTAMP)

            # If there is no timestamp, exclude
            if not ts:
                return False
            
            # If there is a start date provided and the given record is earlier, exclude.
            if start_date and ts < start_date:
                return False

            # If there is an end date provided and the given record is later, exclude.
            if end_date and ts < end_date:
                return False
            
            return True
        
        return [r for r in self.records if in_range(r)]
    

    def get_extra(self, record: LogRecord, key: str, default=None) -> Any:
        '''
        Allows extraction of a key within the extra dictionary if it exists.

        Args:
            record (LogRecord): LogRecord to extrac informatino from.
            key (str): The key within extras to try.
            default: If the key is not in extras of the given LogRecord it returns this value.
        '''
        return record.get("extras", {}).get(key, default)
    

    def top_messages(self, n: int=10) -> List[tuple[str, int]]:
        '''Returns the top n messages and the number of times they occur'''
        counter = Counter(r[ECoreFields.MESSAGE] for r in self.records if ECoreFields.MESSAGE in r)
        return counter.most_common(n)


    def level_counts(self) -> Dict[str, int]:
        '''Returns the _level_counts Counter as a dictionary'''
        return dict(self._level_counts)
    

    def module_counts(self) -> Dict[str, int]:
        '''Returns the _module_counts Counter as a dictionary'''
        return dict(self._module_counts)
    

    def func_counts(self) -> Dict[str, int]:
        '''Returns the _func_counts Counter as a dictionary'''
        return dict(self._func_counts)
    

    def to_dataframe(self, records: List[LogRecord]=None):
        '''Converts either the entire self.records or a given list of records to a pandas dataframe.'''
        import pandas as pd

        rows = []
        records = records if records else self.records
        for record in records:
            row = {k: v for k, v in record.items() if k != ECoreFields.EXTRAS}
            row.update(record.get(ECoreFields.EXTRAS))
            rows.append(row)
        
        return pd.DataFrame(rows)


    def _normalize(self, raw: dict) -> LogRecord:
        '''Converts a raw json dictionary to a normalized LogRecord typed dict'''
        record: LogRecord = {}

        for field in self.CORE_FIELDS:
            # Convert the timestamps to datetime objects
            if field == ECoreFields.TIMESTAMP:
                record["timestamp"] = datetime.fromisoformat(
                raw["timestamp"].replace("Z", "+00:00")
            )
                
            # If the raw dictionary is missinng one of the expected fields add it to the record as an empty string
            elif field not in raw:
                record[field] = '' if not field == ECoreFields.EXTRAS else {}
            
            # For all other expected fields, add raw to the record
            else:
                record[field] = raw[field]
        
        return record
    

    def _record_metrics(self, record: LogRecord) -> None:
        '''Adds the information from the provided record to the parsing metrics'''
        self._level_counts[record[ECoreFields.LEVEL]] += 1
        self._module_counts[record[ECoreFields.MODULE]] += 1
        self._func_counts[record[ECoreFields.FUNCTION]] += 1
    
    
    def __repr__(self):
        return f'{self.__class__.__name__}({os.path.basename(self.file_path)})'
    