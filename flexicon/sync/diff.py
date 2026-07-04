"""
DiffEngine - Object comparison and diff generation

This module provides diff functionality for comparing FLEx objects between projects.

Author: FlexTools Development Team
Date: 2025-11-26
"""

import logging
from typing import List, Optional, Any, Callable, Dict, Set
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Type of change detected"""

    NEW = "new"  # Object exists in source, not in target
    MODIFIED = "modified"  # Object exists in both but differs
    DELETED = "deleted"  # Object exists in target, not in source
    CONFLICT = "conflict"  # Object differs in incompatible ways
    UNCHANGED = "unchanged"  # Object identical in both


@dataclass
class Change:
    """
    Represents a single detected change.

    Attributes:
        change_type: Type of change
        source_guid: GUID of source object (None if deleted)
        target_guid: GUID of target object (None if new)
        object_type: Type of object
        description: Human-readable description
        details: Additional details about the change
    """

    change_type: ChangeType
    source_guid: Optional[str]
    target_guid: Optional[str]
    object_type: str
    description: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def guid(self) -> str:
        """Primary GUID for this change."""
        return self.source_guid or self.target_guid or "unknown"


class DiffResult:
    """
    Results from a diff operation.

    Contains all changes detected, organized by type, with methods for
    analysis and reporting.

    Usage:
        >>> diff = sync.compare(object_type="Allomorph")
        >>>
        >>> print(f"Total changes: {diff.total}")
        >>> print(f"New: {diff.num_new}")
        >>> print(f"Modified: {diff.num_modified}")
        >>>
        >>> for change in diff.new_changes:
        ...     print(f"  {change.description}")
        >>>
        >>> print(diff.summary())
    """

    def __init__(self, object_type: str):
        """
        Initialize DiffResult.

        Args:
            object_type: Type of objects being compared
        """
        self.object_type = object_type
        self.changes: List[Change] = []

    def add_change(self, change: Change) -> None:
        """Add a change to the result."""
        self.changes.append(change)

    @property
    def new_changes(self) -> List[Change]:
        """All NEW changes."""
        return [c for c in self.changes if c.change_type == ChangeType.NEW]

    @property
    def modified_changes(self) -> List[Change]:
        """All MODIFIED changes."""
        return [c for c in self.changes if c.change_type == ChangeType.MODIFIED]

    @property
    def deleted_changes(self) -> List[Change]:
        """All DELETED changes."""
        return [c for c in self.changes if c.change_type == ChangeType.DELETED]

    @property
    def conflict_changes(self) -> List[Change]:
        """All CONFLICT changes."""
        return [c for c in self.changes if c.change_type == ChangeType.CONFLICT]

    @property
    def unchanged_changes(self) -> List[Change]:
        """All UNCHANGED changes."""
        return [c for c in self.changes if c.change_type == ChangeType.UNCHANGED]

    @property
    def num_new(self) -> int:
        """Count of NEW changes."""
        return len(self.new_changes)

    @property
    def num_modified(self) -> int:
        """Count of MODIFIED changes."""
        return len(self.modified_changes)

    @property
    def num_deleted(self) -> int:
        """Count of DELETED changes."""
        return len(self.deleted_changes)

    @property
    def num_conflicts(self) -> int:
        """Count of CONFLICT changes."""
        return len(self.conflict_changes)

    @property
    def num_unchanged(self) -> int:
        """Count of UNCHANGED changes."""
        return len(self.unchanged_changes)

    @property
    def total(self) -> int:
        """Total number of changes (excluding unchanged)."""
        return self.num_new + self.num_modified + self.num_deleted + self.num_conflicts

    @property
    def has_changes(self) -> bool:
        """Whether any changes were detected."""
        return self.total > 0

    @property
    def has_conflicts(self) -> bool:
        """Whether any conflicts were detected."""
        return self.num_conflicts > 0

    def summary(self) -> str:
        """
        Generate a text summary of changes.

        Returns:
            Human-readable summary string

        Example:
            >>> print(diff.summary())
            DIFF SUMMARY: Allomorphs
            ----------------------------------------
            15 NEW (in source, not in target)
            3 MODIFIED (different in source)
            2 DELETED (in target, not in source)
            0 CONFLICTS
        """
        lines = [
            f"DIFF SUMMARY: {self.object_type}",
            "-" * 40,
            f"{self.num_new} NEW (in source, not in target)",
            f"{self.num_modified} MODIFIED (different in source)",
            f"{self.num_deleted} DELETED (in target, not in source)",
            f"{self.num_conflicts} CONFLICTS",
        ]

        if not self.has_changes:
            lines.append("")
            lines.append("No changes detected.")

        return "\n".join(lines)

    def to_report(self, format: str = "console", verbose: bool = False) -> str:
        """
        Generate a detailed report.

        Args:
            format: Report format ("console", "markdown", "html")
            verbose: Include unchanged items

        Returns:
            Formatted report string

        Example:
            >>> print(diff.to_report(format="console", verbose=False))
        """
        if format == "console":
            return self._to_console_report(verbose)
        elif format == "markdown":
            return self._to_markdown_report(verbose)
        else:
            raise ValueError(f"Unknown format: {format}")

    def _to_console_report(self, verbose: bool) -> str:
        """Generate console-formatted report."""
        lines = [self.summary(), ""]

        if self.num_new > 0:
            lines.append(f"NEW {self.object_type.upper()}:")
            for change in self.new_changes:
                lines.append(f"  + {change.description}")
            lines.append("")

        if self.num_modified > 0:
            lines.append(f"MODIFIED {self.object_type.upper()}:")
            for change in self.modified_changes:
                lines.append(f"  ~ {change.description}")
                if change.details:
                    for key, value in change.details.items():
                        lines.append(f"      {key}: {value}")
            lines.append("")

        if self.num_deleted > 0:
            lines.append(f"DELETED {self.object_type.upper()}:")
            for change in self.deleted_changes:
                lines.append(f"  - {change.description}")
            lines.append("")

        if self.num_conflicts > 0:
            lines.append(f"CONFLICTS ({self.num_conflicts}):")
            for change in self.conflict_changes:
                lines.append(f"  ! {change.description}")
            lines.append("")

        if verbose and self.num_unchanged > 0:
            lines.append(f"UNCHANGED ({self.num_unchanged}):")
            for change in self.unchanged_changes:
                lines.append(f"  = {change.description}")

        return "\n".join(lines)

    def _to_markdown_report(self, verbose: bool) -> str:
        """Generate markdown-formatted report."""
        lines = [
            f"# Diff Report: {self.object_type}",
            "",
            "## Summary",
            "",
            f"- **New:** {self.num_new}",
            f"- **Modified:** {self.num_modified}",
            f"- **Deleted:** {self.num_deleted}",
            f"- **Conflicts:** {self.num_conflicts}",
            "",
        ]

        if self.num_new > 0:
            lines.extend(
                [
                    f"## New {self.object_type}",
                    "",
                ]
            )
            for change in self.new_changes:
                lines.append(f"- {change.description}")
            lines.append("")

        if self.num_modified > 0:
            lines.extend(
                [
                    f"## Modified {self.object_type}",
                    "",
                ]
            )
            for change in self.modified_changes:
                lines.append(f"- {change.description}")
            lines.append("")

        if self.num_deleted > 0:
            lines.extend(
                [
                    f"## Deleted {self.object_type}",
                    "",
                ]
            )
            for change in self.deleted_changes:
                lines.append(f"- {change.description}")
            lines.append("")

        if self.num_conflicts > 0:
            lines.extend(
                [
                    f"## Conflicts",
                    "",
                ]
            )
            for change in self.conflict_changes:
                lines.append(f"- {change.description}")
            lines.append("")

        return "\n".join(lines)

    def export(self, filename: str) -> None:
        """
        Export diff report to file.

        Args:
            filename: Output filename (.txt, .md, .html, .csv)

        Example:
            >>> diff.export("allomorph_diff.md")
            >>> diff.export("allomorph_diff.html")
        """
        # Phase 1: Basic export
        # Full export with HTML/CSV in Phase 4
        ext = filename.split(".")[-1].lower()

        if ext == "txt":
            content = self.to_report(format="console", verbose=True)
        elif ext == "md":
            content = self.to_report(format="markdown", verbose=True)
        else:
            raise ValueError(f"Unsupported export format: {ext} (Phase 1 supports .txt, .md)")

        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Exported diff report to {filename}")


class DiffEngine:
    """
    Engine for comparing FLEx objects between projects.

    The DiffEngine compares objects using a match strategy and detects
    all changes (new, modified, deleted, conflicts).

    Usage:
        >>> from flexlibs2.sync import DiffEngine, GuidMatchStrategy
        >>>
        >>> engine = DiffEngine()
        >>> result = engine.compare(
        ...     source_objects=source_project.Allomorph,
        ...     target_objects=target_project.Allomorph,
        ...     source_project=source_project,
        ...     target_project=target_project,
        ...     match_strategy=GuidMatchStrategy()
        ... )
    """

    def compare(
        self,
        source_objects: Any,
        target_objects: Any,
        source_project: Any,
        target_project: Any,
        match_strategy: "MatchStrategy",
        filter_fn: Optional[Callable] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> DiffResult:
        """
        Compare objects between source and target.

        Args:
            source_objects: Source operations class instance
            target_objects: Target operations class instance
            source_project: Source FLExProject
            target_project: Target FLExProject
            match_strategy: Strategy for matching objects
            filter_fn: Optional filter function
            progress_callback: Optional progress callback

        Returns:
            DiffResult with all changes
        """
        # Get object type name
        object_type = source_objects.__class__.__name__.replace("Operations", "")

        result = DiffResult(object_type)

        # Get all objects from both sides
        if progress_callback:
            progress_callback("Loading source objects...")

        source_items = list(source_objects.GetAll())

        if filter_fn:
            source_items = [obj for obj in source_items if filter_fn(obj)]

        if progress_callback:
            progress_callback("Loading target objects...")

        target_items = list(target_objects.GetAll())

        # Build GUID lookup for target objects
        target_by_guid: Dict[str, Any] = {}
        for target_obj in target_items:
            target_guid = str(target_obj.Guid)
            target_by_guid[target_guid] = target_obj

        # Track which target objects were matched
        matched_target_guids: Set[str] = set()

        # Compare source objects
        if progress_callback:
            progress_callback(f"Comparing {len(source_items)} source objects...")

        for i, source_obj in enumerate(source_items):
            if progress_callback and i % 100 == 0:
                progress_callback(f"Comparing {i}/{len(source_items)}...")

            # Try to match with target
            match = match_strategy.match(source_obj, target_items, source_project, target_project)

            if match is None:
                # NEW: Source object doesn't exist in target
                change = self._create_new_change(source_obj, source_objects, object_type)
                result.add_change(change)
            else:
                # Object exists in target
                match_guid = str(match.Guid)
                matched_target_guids.add(match_guid)

                # Check if modified
                is_modified, details = self._compare_objects(
                    source_obj, match, source_objects, target_objects, source_project, target_project
                )

                if is_modified:
                    # MODIFIED: Object differs
                    change = self._create_modified_change(source_obj, match, source_objects, object_type, details)
                    result.add_change(change)
                else:
                    # UNCHANGED: Object identical
                    change = self._create_unchanged_change(source_obj, match, source_objects, object_type)
                    result.add_change(change)

        # Find deleted objects (in target but not matched)
        if progress_callback:
            progress_callback("Finding deleted objects...")

        for target_obj in target_items:
            target_guid = str(target_obj.Guid)
            if target_guid not in matched_target_guids:
                # DELETED: Target object doesn't exist in source
                change = self._create_deleted_change(target_obj, target_objects, object_type)
                result.add_change(change)

        if progress_callback:
            progress_callback("Comparison complete")

        return result

    def _create_new_change(self, source_obj: Any, source_ops: Any, object_type: str) -> Change:
        """Create a NEW change."""
        source_guid = str(source_obj.Guid)

        # Get description (try common methods)
        description = self._get_object_description(source_obj, source_ops)

        return Change(
            change_type=ChangeType.NEW,
            source_guid=source_guid,
            target_guid=None,
            object_type=object_type,
            description=f"NEW: {description}",
        )

    def _create_modified_change(
        self, source_obj: Any, target_obj: Any, source_ops: Any, object_type: str, details: Dict[str, Any]
    ) -> Change:
        """Create a MODIFIED change."""
        source_guid = str(source_obj.Guid)
        target_guid = str(target_obj.Guid)

        description = self._get_object_description(source_obj, source_ops)

        return Change(
            change_type=ChangeType.MODIFIED,
            source_guid=source_guid,
            target_guid=target_guid,
            object_type=object_type,
            description=f"MODIFIED: {description}",
            details=details,
        )

    def _create_deleted_change(self, target_obj: Any, target_ops: Any, object_type: str) -> Change:
        """Create a DELETED change."""
        target_guid = str(target_obj.Guid)

        description = self._get_object_description(target_obj, target_ops)

        return Change(
            change_type=ChangeType.DELETED,
            source_guid=None,
            target_guid=target_guid,
            object_type=object_type,
            description=f"DELETED: {description}",
        )

    def _create_unchanged_change(self, source_obj: Any, target_obj: Any, source_ops: Any, object_type: str) -> Change:
        """Create an UNCHANGED change."""
        source_guid = str(source_obj.Guid)
        target_guid = str(target_obj.Guid)

        description = self._get_object_description(source_obj, source_ops)

        return Change(
            change_type=ChangeType.UNCHANGED,
            source_guid=source_guid,
            target_guid=target_guid,
            object_type=object_type,
            description=f"UNCHANGED: {description}",
        )

    def _get_object_description(self, obj: Any, ops: Any) -> str:
        """Get human-readable description of object."""
        # Try common description methods
        if hasattr(ops, "GetForm"):
            try:
                return ops.GetForm(obj)
            except (AttributeError, KeyError):
                pass

        if hasattr(ops, "GetHeadword"):
            try:
                return ops.GetHeadword(obj)
            except (AttributeError, KeyError):
                pass

        if hasattr(ops, "GetName"):
            try:
                return ops.GetName(obj)
            except (AttributeError, KeyError):
                pass

        # Fallback to GUID
        return f"Object {str(obj.Guid)[:8]}..."

    def _compare_objects(
        self,
        source_obj: Any,
        target_obj: Any,
        source_ops: Any,
        target_ops: Any,
        source_project: Any,
        target_project: Any,
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Compare two objects to detect modifications.

        Returns:
            (is_modified, details_dict)
        """
        details = {}
        is_modified = False

        # Try to use CompareTo() method if available (sync framework integration)
        # CompareTo() provides detailed property-level comparison using GetSyncableProperties()
        if hasattr(source_ops, "CompareTo"):
            try:
                # Call CompareTo with both operation instances for cross-project comparison
                # Returns: (is_different, differences_dict) where differences_dict maps
                # property names to (value1, value2) tuples
                is_different, differences = source_ops.CompareTo(
                    source_obj, target_obj, ops1=source_ops, ops2=target_ops
                )

                if is_different:
                    is_modified = True
                    # Convert differences format from (val1, val2) to "val1 → val2" for display
                    for prop, (val1, val2) in differences.items():
                        # Format MultiString dicts and other values appropriately
                        if isinstance(val1, dict) and isinstance(val2, dict):
                            # MultiString comparison - show which writing systems differ
                            all_ws = set(val1.keys()) | set(val2.keys())
                            diff_ws = [ws for ws in all_ws if val1.get(ws) != val2.get(ws)]
                            if diff_ws:
                                details[prop] = f"Changed in {len(diff_ws)} writing system(s)"
                        else:
                            details[prop] = f"{val2} → {val1}"

                # Return early if CompareTo() succeeded
                return is_modified, details

            except Exception as e:
                # Log error but fall through to basic comparison
                logger.debug(f"CompareTo() failed, falling back to basic comparison: {e}")

        # Fallback: Basic comparison for classes without CompareTo()
        # This preserves backwards compatibility with operation classes that
        # haven't implemented the sync framework methods yet

        # Try form comparison (for Allomorphs, etc.)
        if hasattr(source_ops, "GetForm"):
            try:
                source_form = source_ops.GetForm(source_obj)
                target_form = target_ops.GetForm(target_obj)
                if source_form != target_form:
                    is_modified = True
                    details["Form"] = f"{target_form} → {source_form}"
            except (AttributeError, KeyError):
                pass

        # Try name comparison (for POS, etc.)
        if hasattr(source_ops, "GetName"):
            try:
                source_name = source_ops.GetName(source_obj)
                target_name = target_ops.GetName(target_obj)
                if source_name != target_name:
                    is_modified = True
                    details["Name"] = f"{target_name} → {source_name}"
            except (AttributeError, KeyError):
                pass

        return is_modified, details
