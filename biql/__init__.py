"""
BIQL - BIDS Query Language

A powerful query language for Brain Imaging Data Structure (BIDS) datasets.
"""

__version__ = "0.1.0"
__author__ = "BIQL Development Team"

from .dataset import BIDSDataset
from .evaluator import BIQLEvaluator
from .formatter import BIQLFormatter
from .parser import BIQLParser
from .query import BIQLQuery, create_query_engine
from .utils import create_example_dataset

__all__ = [
    "BIQLParser",
    "BIQLEvaluator",
    "BIDSDataset",
    "BIQLFormatter",
    "BIQLQuery",
    "create_query_engine",
    "create_example_dataset",
]
