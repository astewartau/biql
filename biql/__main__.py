"""
Main entry point for BIQL package when run as module.
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
