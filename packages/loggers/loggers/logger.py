"""
logger.py

Class:
    Logger: a basic logging class for cleanly handling logging for a specific class or module
"""
import logging
from typing import List, Dict, Union

# Configure logging (best practice for debugging and monitoring)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class Logger:
    """
    A logging class that uses singleton-like behavior to avoid creating duplicate loggers.
    Allows changing logging output location and level
    """
    # Initialize instances dictionary
    _instances = {}


    def __new__(cls, name, level=logging.INFO, log_to_file: bool=False):
        """
        creates memory for the new object before __init__() is called. used in this case to control instance creation

        Args:
            cls: refers to the class itself, always an argument in the __new__ method for classes
                (like self for __init__ method)  
            name (str): the name of the logger instance being created, will be added to _instances{}
            level: sets the output logging level for the logger at creation, can be changed during runtime using
                logger.setLevel(logger.LEVEL)
            log_to_file (bool): default False. if False no file handler created, if True automatic log file created using standard format
        
        Returns:
            None
        """
        # TODO: Add descriptions of what each code block does here
        if name in cls._instances:
            return cls._instances[name]
        
        instance = super(Logger, cls).__new__(cls)
        instance.logger = logging.getLogger(name)
        instance.logger.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        instance.logger.addHandler(console_handler)

        # File handler (if specified)
        if log_to_file:
            # TODO: Create a automatic log file generation in the docs/logs folder
            file_handler = logging.FileHandler(log_to_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            instance.logger.addHandler(file_handler)

        cls._instances[name] = instance
        return instance


    def get_logger(self):
        return self.logger




def sample_function(data: List[int]) -> Dict[str, Union[int, float]]:
    """
    A sample function that performs basic calculations on a list of numbers.

    Args:
        data (List[int]): A list of integers.

    Returns:
        Dict[str, Union[int, float]]: A dictionary containing calculated metrics.
    """
    if not data:
        logging.warning("Data list is empty.")
        return {"count": 0, "average": 0.0}

    return {
        "count": len(data),
        "average": sum(data) / len(data)
    }


if __name__ == "__main__":
    # Example usage and testing
    logging.info("Executing module_template.py as a standalone script.")

    instance = Logger("test")
    print(instance.display())

    sample_data = [10, 20, 30, 40, 50]
    results = sample_function(sample_data)
    print(results)
