import sys
from pathlib import Path

# Ensure the loggers package is imported from the repo, not the tests directory
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))