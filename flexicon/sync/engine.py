"""
SyncEngine - Core orchestrator for multi-database synchronization

This module provides the main SyncEngine class that coordinates all sync operations.

Author: FlexTools Development Team
Date: 2025-11-26
"""

import logging
from typing import Optional, Union, Any, Callable
from enum import Enum

from .diff import DiffEngine, DiffResult
from .match_strategies import MatchStrategy, GuidMatchStrategy
from .conflict_resolvers import ConflictResolver, SourceWinsResolver

logger = logging.getLogger(__name__)


class SyncMode(Enum):
    """Sync operation mode"""

    READONLY = "readonly"  # Diff only, no writes
    WRITE = "write"  # Execute sync operations


class SyncEngine:
    """
    Main orchestrator for database synchronization operations.

    The SyncEngine coordinates comparison and synchronization of FLEx objects
    between two projects. It respects the writeEnabled flag from FlexTools
    to determine whether to show diffs (readonly) or execute syncs (write).

    Usage:
        >>> from flexlibs2.sync import SyncEngine, GuidMatchStrategy
        >>>
        >>> # Create engine
        >>> sync = SyncEngine(
        ...     source_project=source_project,
        ...     target_project=target_project
        ... )
        >>>
        >>> # Readonly mode - show diff only
        >>> diff = sync.compare(
        ...     object_type="Allomorph",
        ...     match_strategy=GuidMatchStrategy()
        ... )
        >>> print(diff.summary())
        >>>
        >>> # Write mode - execute sync
        >>> result = sync.sync(
        ...     object_type="Allomorph",
        ...     match_strategy=GuidMatchStrategy(),
        ...     conflict_resolver="source_wins"
        ... )
    """

    def __init__(self, source_project: Any, target_project: Any, mode: Optional[SyncMode] = None):
        """
        Initialize SyncEngine.

        Args:
            source_project: Source FLExProject instance
            target_project: Target FLExProject instance
            mode: Optional explicit mode. If None, auto-detect from target.writeEnabled

        Example:
            >>> sync = SyncEngine(
            ...     source_project=source,
            ...     target_project=target
            ... )
        """
        self.source_project = source_project
        self.target_project = target_project

        # Auto-detect mode from target project if not specified
        if mode is None:
            if hasattr(target_project, "writeEnabled"):
                self.mode = SyncMode.WRITE if target_project.writeEnabled else SyncMode.READONLY
            else:
                # Default to readonly for safety
                self.mode = SyncMode.READONLY
        else:
            self.mode = mode

        # Initialize diff engine
        self.diff_engine = DiffEngine()

        # Registry for custom match strategies
        self._match_strategies = {
            "guid": GuidMatchStrategy(),
        }

        # Registry for conflict resolvers
        self._conflict_resolvers = {
            "source_wins": SourceWinsResolver(),
        }

        logger.info(
            f"SyncEngine initialized in {self.mode.value} mode "
            f"(source: {self._get_project_name(source_project)}, "
            f"target: {self._get_project_name(target_project)})"
        )

    def _get_project_name(self, project: Any) -> str:
        """Get project name for logging."""
        if hasattr(project, "ProjectName"):
            return project.ProjectName()
        return "unknown"

    def register_strategy(self, name: str, strategy: MatchStrategy) -> None:
        """
        Register a custom match strategy.

        Args:
            name: Strategy name for later reference
            strategy: MatchStrategy instance

        Example:
            >>> class CustomMatcher(MatchStrategy):
            ...     def match(self, source_obj, target_candidates, source_project, target_project):
            ...         # Custom matching logic
            ...         pass
            >>>
            >>> sync.register_strategy("custom", CustomMatcher())
            >>> diff = sync.compare(object_type="Entry", match_strategy="custom")
        """
        self._match_strategies[name] = strategy
        logger.debug(f"Registered match strategy: {name}")

    def register_resolver(self, name: str, resolver: ConflictResolver) -> None:
        """
        Register a custom conflict resolver.

        Args:
            name: Resolver name for later reference
            resolver: ConflictResolver instance
        """
        self._conflict_resolvers[name] = resolver
        logger.debug(f"Registered conflict resolver: {name}")

    def _resolve_strategy(self, match_strategy: Union[str, MatchStrategy]) -> MatchStrategy:
        """Resolve match strategy from name or instance."""
        if isinstance(match_strategy, str):
            if match_strategy not in self._match_strategies:
                raise ValueError(
                    f"Unknown match strategy: {match_strategy}. " f"Available: {list(self._match_strategies.keys())}"
                )
            return self._match_strategies[match_strategy]
        return match_strategy

    def _resolve_resolver(self, conflict_resolver: Union[str, ConflictResolver]) -> ConflictResolver:
        """Resolve conflict resolver from name or instance."""
        if isinstance(conflict_resolver, str):
            if conflict_resolver not in self._conflict_resolvers:
                raise ValueError(
                    f"Unknown conflict resolver: {conflict_resolver}. "
                    f"Available: {list(self._conflict_resolvers.keys())}"
                )
            return self._conflict_resolvers[conflict_resolver]
        return conflict_resolver

    def compare(
        self,
        object_type: str,
        match_strategy: Union[str, MatchStrategy, None] = None,
        filter_fn: Optional[Callable] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> DiffResult:
        """
        Compare objects between source and target projects (readonly).

        This method performs a diff-only operation, showing what would change
        if a sync were executed. It never modifies the target database.

        Args:
            object_type: Type of objects to compare (e.g., "Allomorph", "LexEntry")
            match_strategy: Strategy for matching objects (default: GUID-based)
            filter_fn: Optional filter function to include only specific objects
            progress_callback: Optional callback for progress updates

        Returns:
            DiffResult containing all changes detected

        Example:
            >>> diff = sync.compare(
            ...     object_type="Allomorph",
            ...     match_strategy=GuidMatchStrategy()
            ... )
            >>>
            >>> print(f"New: {diff.num_new}")
            >>> print(f"Modified: {diff.num_modified}")
            >>> print(f"Deleted: {diff.num_deleted}")
        """
        # Default to GUID strategy
        if match_strategy is None:
            match_strategy = GuidMatchStrategy()
        else:
            match_strategy = self._resolve_strategy(match_strategy)

        if progress_callback:
            progress_callback(f"Comparing {object_type} objects...")

        # Get operations class for this object type
        source_ops = self._get_operations(self.source_project, object_type)
        target_ops = self._get_operations(self.target_project, object_type)

        # Perform diff
        diff_result = self.diff_engine.compare(
            source_objects=source_ops,
            target_objects=target_ops,
            source_project=self.source_project,
            target_project=self.target_project,
            match_strategy=match_strategy,
            filter_fn=filter_fn,
            progress_callback=progress_callback,
        )

        logger.info(
            f"Comparison complete: {diff_result.num_new} new, "
            f"{diff_result.num_modified} modified, "
            f"{diff_result.num_deleted} deleted, "
            f"{diff_result.num_conflicts} conflicts"
        )

        return diff_result

    def sync(
        self,
        object_type: str,
        match_strategy: Union[str, MatchStrategy, None] = None,
        conflict_resolver: Union[str, ConflictResolver] = "source_wins",
        include_dependencies: bool = False,
        filter_fn: Optional[Callable] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        dry_run: bool = False,
    ) -> "SyncResult":
        """
        Synchronize objects from source to target project (write mode).

        This method executes sync operations, creating/updating/deleting objects
        in the target project. Requires target project opened with writeEnabled=True.

        Args:
            object_type: Type of objects to sync
            match_strategy: Strategy for matching objects (default: GUID-based)
            conflict_resolver: How to resolve conflicts (default: "source_wins")
            include_dependencies: Auto-create missing dependencies (default: False)
            filter_fn: Optional filter function
            progress_callback: Optional callback for progress updates
            dry_run: If True, show what would happen without making changes

        Returns:
            SyncResult with statistics and details

        Raises:
            RuntimeError: If in readonly mode or target not writable

        Example:
            >>> result = sync.sync(
            ...     object_type="Allomorph",
            ...     match_strategy=GuidMatchStrategy(),
            ...     conflict_resolver="source_wins"
            ... )
            >>>
            >>> print(f"Created: {result.num_created}")
            >>> print(f"Updated: {result.num_updated}")
            >>> print(f"Deleted: {result.num_deleted}")
        """
        # Check if write operations are allowed
        if self.mode == SyncMode.READONLY:
            raise RuntimeError("Cannot sync in readonly mode. " "Open target project with writeEnabled=True")

        if hasattr(self.target_project, "writeEnabled") and not self.target_project.writeEnabled:
            raise RuntimeError("Target project not opened with writeEnabled=True")

        # Phase 2: Full sync implementation
        from .merge_ops import MergeOperations, SyncChange, SyncError

        # Default to GUID strategy if not specified
        if match_strategy is None:
            match_strategy = GuidMatchStrategy()
        else:
            match_strategy = self._resolve_strategy(match_strategy)

        # Resolve conflict resolver
        conflict_resolver = self._resolve_resolver(conflict_resolver)

        # Initialize result tracking
        result = SyncResult(object_type)

        # Initialize merge operations
        merger = MergeOperations(self.target_project)

        try:
            if progress_callback:
                progress_callback(f"Starting sync of {object_type}...")

            # Step 1: Perform comparison to identify changes
            if progress_callback:
                progress_callback("Comparing objects...")

            diff = self.compare(
                object_type=object_type,
                match_strategy=match_strategy,
                filter_fn=filter_fn,
                progress_callback=None,  # Don't duplicate progress
            )

            # Get operations classes
            source_ops = self._get_operations(self.source_project, object_type)
            target_ops = self._get_operations(self.target_project, object_type)

            total_operations = diff.num_new + diff.num_modified + diff.num_deleted
            current = 0

            # Step 2: Create new objects
            if diff.num_new > 0:
                if progress_callback:
                    progress_callback(f"Creating {diff.num_new} new objects...")

                for change in diff.new_changes:
                    current += 1
                    if progress_callback and current % 10 == 0:
                        progress_callback(f"Progress: {current}/{total_operations}")

                    try:
                        # Get source object by GUID
                        source_obj = self.source_project.Object(change.source_guid)

                        # Create in target (details vary by object type)
                        # For now, we skip objects that need parents (Phase 3 dependency handling)
                        if not dry_run:
                            created_obj = merger.create_object(
                                target_ops=target_ops, source_obj=source_obj, source_ops=source_ops
                            )

                            result.add_change(
                                SyncChange(operation="create", object_type=object_type, object_guid=change.source_guid)
                            )
                        else:
                            result.skip()

                    except Exception as e:
                        logger.error(f"Failed to create object {change.source_guid}: {e}")
                        result.add_error(
                            SyncError(operation="create", object_guid=change.source_guid, error_message=str(e))
                        )

            # Step 3: Update modified objects
            if diff.num_modified > 0:
                if progress_callback:
                    progress_callback(f"Updating {diff.num_modified} modified objects...")

                for change in diff.modified_changes:
                    current += 1
                    if progress_callback and current % 10 == 0:
                        progress_callback(f"Progress: {current}/{total_operations}")

                    try:
                        # Get both objects
                        source_obj = self.source_project.Object(change.source_guid)
                        target_obj = self.target_project.Object(change.target_guid)

                        # Apply conflict resolution
                        resolved_obj = conflict_resolver.resolve(
                            source_obj, target_obj, self.source_project, self.target_project
                        )

                        # If source wins, update target from source
                        if resolved_obj == source_obj and not dry_run:
                            changed = merger.update_object(
                                target_obj=target_obj,
                                source_obj=source_obj,
                                source_ops=source_ops,
                                target_ops=target_ops,
                            )

                            if changed:
                                result.add_change(
                                    SyncChange(
                                        operation="update",
                                        object_type=object_type,
                                        object_guid=change.target_guid,
                                        details=change.details,
                                    )
                                )
                            else:
                                result.skip()
                        else:
                            # Target wins or no changes needed
                            result.skip()

                    except Exception as e:
                        logger.error(f"Failed to update object {change.target_guid}: {e}")
                        result.add_error(
                            SyncError(operation="update", object_guid=change.target_guid, error_message=str(e))
                        )

            # Step 4: Delete removed objects (optional, controlled by user)
            # For safety, we skip deletes by default unless explicitly requested
            # This prevents accidental data loss
            if diff.num_deleted > 0:
                if progress_callback:
                    progress_callback(f"Skipping {diff.num_deleted} deleted objects (safety)")
                result.num_skipped += diff.num_deleted

            if progress_callback:
                progress_callback("Sync complete")

            logger.info(
                f"Sync completed: {result.num_created} created, "
                f"{result.num_updated} updated, {result.num_errors} errors"
            )

            return result

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            result.add_error(SyncError(operation="sync", object_guid=None, error_message=f"Sync operation failed: {e}"))
            return result

    def _get_operations(self, project: Any, object_type: str) -> Any:
        """
        Get operations class for object type.

        Args:
            project: FLExProject instance
            object_type: Object type name (e.g., "Allomorph", "LexEntry")

        Returns:
            Operations instance

        Raises:
            AttributeError: If object type not found
        """
        # Map common object type names to operations classes
        type_mapping = {
            "Allomorph": "Allomorph",
            "LexEntry": "LexEntry",
            "LexSense": "LexSense",
            "Example": "Example",
            "POS": "POS",
            "Phoneme": "Phoneme",
            "PhonologicalRule": "PhonologicalRule",
            "NaturalClass": "NaturalClass",
            # Add more as needed
        }

        ops_name = type_mapping.get(object_type, object_type)

        if not hasattr(project, ops_name):
            raise AttributeError(
                f"Project does not have '{ops_name}' operations. "
                f"Available: {[attr for attr in dir(project) if not attr.startswith('_')]}"
            )

        return getattr(project, ops_name)

    def compare_possibility_list(
        self, list_type: str, match_strategy: Union[str, MatchStrategy, None] = None
    ) -> DiffResult:
        """
        Compare possibility lists (POS, MorphTypes, etc.) between projects.

        Args:
            list_type: Type of possibility list (e.g., "PartsOfSpeech")
            match_strategy: Strategy for matching (default: GUID-based)

        Returns:
            DiffResult for the possibility list

        Note:
            This is a specialized comparison for hierarchical possibility lists.
            Full implementation in Phase 4.
        """
        raise NotImplementedError("Possibility list comparison not yet implemented (Phase 4)")

    def validate_dependencies(self, object_type: str, auto_create_missing: bool = False) -> "DependencyValidation":
        """
        Validate that all dependencies exist in target project.

        Args:
            object_type: Type of objects to validate
            auto_create_missing: If True, auto-create missing dependencies

        Returns:
            DependencyValidation result

        Note:
            Full implementation in Phase 3 (Dependency Safety).
        """
        raise NotImplementedError("Dependency validation not yet implemented (Phase 3)")

    def create_snapshot(self, project: Any) -> "Snapshot":
        """
        Create a snapshot for rollback.

        Args:
            project: Project to snapshot

        Returns:
            Snapshot instance

        Note:
            Full implementation in Phase 4 (Undo/Rollback).
        """
        raise NotImplementedError("Snapshot creation not yet implemented (Phase 4)")


class SyncResult:
    """
    Results from a sync operation.

    Tracks all changes made during a sync, including creates, updates,
    deletes, and any errors encountered.

    Usage:
        >>> result = sync.sync(object_type="Allomorph")
        >>> print(f"Created: {result.num_created}")
        >>> print(f"Updated: {result.num_updated}")
        >>> result.export_log("sync_log.txt")
    """

    def __init__(self, object_type: str):
        """
        Initialize SyncResult.

        Args:
            object_type: Type of objects being synced
        """
        self.object_type = object_type
        self.num_created = 0
        self.num_updated = 0
        self.num_deleted = 0
        self.num_skipped = 0
        self.num_errors = 0

        from .merge_ops import SyncChange, SyncError

        self.changes: List[SyncChange] = []
        self.errors: List[SyncError] = []

    @property
    def total(self) -> int:
        """Total number of operations performed."""
        return self.num_created + self.num_updated + self.num_deleted

    @property
    def success(self) -> bool:
        """Whether sync completed without errors."""
        return self.num_errors == 0

    def add_change(self, change: "SyncChange") -> None:
        """Record a change made during sync."""
        self.changes.append(change)

        # Update counters
        if change.operation == "create":
            self.num_created += 1
        elif change.operation == "update":
            self.num_updated += 1
        elif change.operation == "delete":
            self.num_deleted += 1

    def add_error(self, error: "SyncError") -> None:
        """Record an error during sync."""
        self.errors.append(error)
        self.num_errors += 1

    def skip(self) -> None:
        """Increment skipped counter."""
        self.num_skipped += 1

    def summary(self) -> str:
        """Generate text summary of sync results."""
        lines = [
            f"SYNC RESULT: {self.object_type}",
            "-" * 40,
            f"Created: {self.num_created}",
            f"Updated: {self.num_updated}",
            f"Deleted: {self.num_deleted}",
            f"Skipped: {self.num_skipped}",
            f"Errors: {self.num_errors}",
            f"Total: {self.total}",
            "",
        ]

        if self.success:
            lines.append("✅ Sync completed successfully")
        else:
            lines.append(f"⚠️ Sync completed with {self.num_errors} errors")

        return "\n".join(lines)

    def export_log(self, filename: str) -> None:
        """
        Export sync log to file.

        Args:
            filename: Output filename

        Example:
            >>> result.export_log("allomorph_sync.log")
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Sync Log: {self.object_type}\n")
            f.write(f"Date: {import_datetime()}\n")
            f.write("=" * 60 + "\n\n")

            f.write(self.summary() + "\n\n")

            if self.changes:
                f.write("CHANGES:\n")
                f.write("-" * 40 + "\n")
                for change in self.changes:
                    f.write(f"{change.operation.upper()}: {change.object_guid}\n")
                    if change.details:
                        for key, value in change.details.items():
                            f.write(f"  {key}: {value}\n")
                f.write("\n")

            if self.errors:
                f.write("ERRORS:\n")
                f.write("-" * 40 + "\n")
                for error in self.errors:
                    f.write(f"{error.operation}: {error.error_message}\n")
                    if error.object_guid:
                        f.write(f"  GUID: {error.object_guid}\n")

        logger.info(f"Exported sync log to {filename}")


def import_datetime():
    """Helper to get current datetime."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DependencyValidation:
    """
    Results from dependency validation.

    Phase 3 implementation placeholder.
    """

    pass


class Snapshot:
    """
    Database snapshot for rollback.

    Phase 4 implementation placeholder.
    """

    pass
