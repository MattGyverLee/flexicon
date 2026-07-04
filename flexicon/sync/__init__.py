"""
Multi-Database Sync/Merge Framework for flexlibs

This package provides tools for synchronizing and merging FLEx database objects
between projects, with support for FlexTools integration, conflict resolution,
and dependency management.

Author: FlexTools Development Team
Date: 2025-11-26
"""

from .engine import SyncEngine, SyncResult
from .diff import DiffEngine, DiffResult, ChangeType
from .match_strategies import (
    MatchStrategy,
    GuidMatchStrategy,
    FieldMatchStrategy,
)
from .conflict_resolvers import (
    ConflictResolver,
    SourceWinsResolver,
    TargetWinsResolver,
    ManualResolver,
)
from .export import ReportExporter
from .merge_ops import MergeOperations, SyncChange, SyncError
from .validation import (
    LinguisticValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    ValidationError,
)
from .selective_import import SelectiveImport
from .dependency_graph import (
    DependencyGraph,
    DependencyType,
    DependencyNode,
    CircularDependencyError,
)
from .dependency_resolver import DependencyResolver, DependencyConfig
from .hierarchical_importer import HierarchicalImporter

__version__ = "2.1.0"  # Aligned with flexlibs2 v2.1

__all__ = [
    # Core engine
    "SyncEngine",
    "SyncResult",
    # Diff functionality
    "DiffEngine",
    "DiffResult",
    "ChangeType",
    # Match strategies
    "MatchStrategy",
    "GuidMatchStrategy",
    "FieldMatchStrategy",
    # Conflict resolution
    "ConflictResolver",
    "SourceWinsResolver",
    "TargetWinsResolver",
    "ManualResolver",
    # Export
    "ReportExporter",
    # Merge operations (Phase 2)
    "MergeOperations",
    "SyncChange",
    "SyncError",
    # Linguistic safety (Phase 2.5)
    "LinguisticValidator",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    "ValidationError",
    "SelectiveImport",
    # Dependency management (Phase 3)
    "DependencyGraph",
    "DependencyType",
    "DependencyNode",
    "CircularDependencyError",
    "DependencyResolver",
    "DependencyConfig",
    "HierarchicalImporter",
]
