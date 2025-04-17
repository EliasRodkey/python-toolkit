"""
common.py

A python module which contains generic functions related to the logger and super_logger classes

functions:
    
"""
import logging
from typing import List, Dict, Union

# Configure logging (best practice for debugging and monitoring)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def create_log_filename(run_id: str) -> str:
    """
    a function that uses current datetime and program run id to create a new log filename

    Args:
        run_id (str): A string which defines a way to identify the program run

    Returns:
        str: a log filename ending in .log
    """
    pass


if __name__ == "__main__":
    # Example usage and testing
    logging.info("Executing module_template.py as a standalone script.")


    sample_data = [10, 20, 30, 40, 50]
    results = create_log_filename()
    print(results)
