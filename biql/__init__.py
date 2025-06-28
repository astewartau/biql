"""
BIQL - BIDS Query Language

A powerful query language for Brain Imaging Data Structure (BIDS) datasets.
"""

__version__ = "0.1.0"
__author__ = "BIQL Development Team"

from .parser import BQLParser
from .evaluator import BQLEvaluator
from .dataset import BIDSDataset
from .formatter import BQLFormatter

__all__ = ["BQLParser", "BQLEvaluator", "BIDSDataset", "BQLFormatter"]