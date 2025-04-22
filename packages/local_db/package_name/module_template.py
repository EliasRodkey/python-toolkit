"""
module_template.py

A well-structured Python module template following industry best practices.
include function and class names and descriptions here
"""
import logging
from typing import List, Dict, Union

# Configure logging (best practice for debugging and monitoring)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class MyClass:
    """
    A template class representing an example entity.

    Attributes:
        name (str): The name of the entity.
        value (int): A numeric value associated with the entity.
    """


    def __init__(self, name: str, value: int) -> None:
        """
        Initializes an instance of MyClass.

        Args:
            name (str): The name of the entity.
            value (int): A numeric value associated with the entity.
        """
        self.name = name
        self.value = value
        logging.info(f"Created MyClass instance: {self.name} with value {self.value}")


    def display(self) -> str:
        """
        Returns a formatted string representation of the entity.

        Returns:
            str: A descriptive string with class attributes.
        """
        return f"MyClass(name={self.name}, value={self.value})"



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

    instance = MyClass(name="Example", value=42)
    print(instance.display())

    sample_data = [10, 20, 30, 40, 50]
    results = sample_function(sample_data)
    print(results)
