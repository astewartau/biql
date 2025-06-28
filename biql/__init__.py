"""
BIQL - BIDS Query Language

A powerful query language for Brain Imaging Data Structure (BIDS) datasets.
"""

__version__ = "0.1.0"
__author__ = "BIQL Development Team"

from .parser import BIQLParser
from .evaluator import BIQLEvaluator
from .dataset import BIDSDataset
from .formatter import BIQLFormatter

__all__ = ["BIQLParser", "BIQLEvaluator", "BIDSDataset", "BIQLFormatter"]