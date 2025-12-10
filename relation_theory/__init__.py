"""
Relation Theory Module

This module provides tools for working with relational database theory concepts,
including functional dependencies, relation schemas, and normal form analysis.

Main Components:
- FD: Functional Dependency class
- FDSet: Functional Dependency Set class
- RelationSchema: Relation Schema class with normalization analysis

Example:
    >>> from relation_theory import RelationSchema
    >>> rs = RelationSchema.from_str("ABC", ["A->B", "B->C"])
    >>> keys = rs.candidate_keys()
    >>> level, violations = rs.judge_NF()
"""

from .fd import FD, FDSet
from .rs import RelationSchema

__version__ = "0.1.0"
__author__ = "LinkWanna"
__all__ = ["FD", "FDSet", "RelationSchema"]
