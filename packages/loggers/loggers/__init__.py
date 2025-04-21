# Keep it minimal
# Define metadata clearly
# Provide convenient package-level imports


# Import specific functions or classes for direct access at a package level
from .logger import Logger
from .utils import ELoggingFormats

# Define package-level variables
__version__ = '0.1.0'
__Author__ = 'Elias Rodkey'

# if dependencies are needed for the pacakge handle them carefully
# try:
#     import numpy as np
# except ImportError:
#     raise RuntimeError("numpy is required for this package but not installed.")
