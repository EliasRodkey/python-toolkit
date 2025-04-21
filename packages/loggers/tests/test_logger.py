"""
test_loggers.py

Unit tests for logger.py using pytest.
"""
import sys
sys.path.insert(0, '.')

import pytest
from loggers.logger import Logger


# Global Variables
TEST_LOGGER_NAME_1 = 'test_1'
TEST_LOGGER_NAME_2 = 'test_2'
TEST_LOGGER_NAME_3 = 'test_3'


# Test Class for Logger
class TestLogger:
    """Unit tests for Logger."""

    def test_singleton_like(self):
        """Test if Logger singleton like"""
        logger_1 = Logger(TEST_LOGGER_NAME_1, run_name = 'test')
        logger_2 = Logger(TEST_LOGGER_NAME_1, run_name = 'test')
        logger_3 = Logger(TEST_LOGGER_NAME_1, run_name = 'test')

        assert logger_1.logger == logger_2.logger
        assert logger_2.logger == logger_3.logger
        assert logger_3.logger == logger_1.logger

    # def test_display_method(self):
    #     """Test if display() returns the correct string format."""
    #     obj = Logger(name="Sample", value=42)
    #     expected_output = "Logger(name=Sample, value=42)"
    #     assert obj.display() == expected_output


# # Test Function for sample_function
# @pytest.mark.parametrize(
#     "data, expected",
#     [
#         ([1, 2, 3, 4], {"count": 4, "average": 2.5}),
#         ([10, 20, 30], {"count": 3, "average": 20.0}),
#         ([], {"count": 0, "average": 0.0}),
#     ],
# )
# def test_sample_function(data, expected):
#     """Test sample_function with various inputs."""
#     assert sample_function(data) == expected