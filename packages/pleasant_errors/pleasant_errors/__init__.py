from pleasant_errors.catch import catch
from pleasant_errors.models import Error, StructuredError
from pleasant_errors.result import Err, Ok, Result

# Metadata
__version__ = "1.0.0"
__author__ = "Elias Rodkey"

__all__ = [
    "catch",
    "Ok",
    "Err",
    "Result",
    "Error",
    "StructuredError",
]
