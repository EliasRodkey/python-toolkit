"""
test_module_template.py

Unit tests for module_template.py using pytest.

Author: Elias
"""

import pytest
from super_logger.logger import MyClass, sample_function


# Test Class for MyClass
class TestMyClass:
    """Unit tests for MyClass."""

    def test_instance_creation(self):
        """Test if MyClass initializes correctly."""
        obj = MyClass(name="Test", value=100)
        assert obj.name == "Test"
        assert obj.value == 100

    def test_display_method(self):
        """Test if display() returns the correct string format."""
        obj = MyClass(name="Sample", value=42)
        expected_output = "MyClass(name=Sample, value=42)"
        assert obj.display() == expected_output


# Test Function for sample_function
@pytest.mark.parametrize(
    "data, expected",
    [
        ([1, 2, 3, 4], {"count": 4, "average": 2.5}),
        ([10, 20, 30], {"count": 3, "average": 20.0}),
        ([], {"count": 0, "average": 0.0}),
    ],
)
def test_sample_function(data, expected):
    """Test sample_function with various inputs."""
    assert sample_function(data) == expected


# Run tests (if not using pytest directly)
if __name__ == "__main__":
    pytest.main()
