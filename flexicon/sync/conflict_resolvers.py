"""
Conflict Resolvers - Strategies for resolving sync conflicts

This module provides conflict resolution policies for sync operations.

Author: FlexTools Development Team
Date: 2025-11-26
"""

import logging
from typing import Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ConflictResolver(ABC):
    """
    Base class for conflict resolution strategies.

    When an object exists in both source and target but differs, a conflict
    resolver determines which version to keep.

    Custom resolvers can be implemented by subclassing and implementing resolve().
    """

    @abstractmethod
    def resolve(self, source_obj: Any, target_obj: Any, source_project: Any, target_project: Any) -> Any:
        """
        Resolve conflict between source and target objects.

        Args:
            source_obj: Source version of object
            target_obj: Target version of object
            source_project: Source FLExProject instance
            target_project: Target FLExProject instance

        Returns:
            The object to keep (either source_obj or target_obj)
        """
        pass


class SourceWinsResolver(ConflictResolver):
    """
    Resolve conflicts by always choosing the source version.

    This is the most common strategy for one-way sync operations where
    the source is considered authoritative.

    Use this when:
    - Source is the "master" or "stable" project
    - Syncing updates from development to production
    - You want to overwrite target with source data

    Example:
        >>> resolver = SourceWinsResolver()
        >>> sync.sync(
        ...     object_type="Allomorph",
        ...     conflict_resolver=resolver
        ... )
    """

    def resolve(self, source_obj: Any, target_obj: Any, source_project: Any, target_project: Any) -> Any:
        """
        Always choose source version.

        Args:
            source_obj: Source object (will be chosen)
            target_obj: Target object (will be overwritten)
            source_project: Source project
            target_project: Target project

        Returns:
            source_obj
        """
        logger.debug(f"Conflict resolved: source wins (GUID: {source_obj.Guid})")
        return source_obj


class TargetWinsResolver(ConflictResolver):
    """
    Resolve conflicts by always keeping the target version.

    This strategy preserves the target project's data when conflicts occur.
    Useful for selective merging or when target has priority.

    Use this when:
    - Target contains more recent data
    - You want to preserve local changes
    - Syncing metadata but keeping target content

    Example:
        >>> resolver = TargetWinsResolver()
        >>> sync.sync(
        ...     object_type="Allomorph",
        ...     conflict_resolver=resolver
        ... )
    """

    def resolve(self, source_obj: Any, target_obj: Any, source_project: Any, target_project: Any) -> Any:
        """
        Always keep target version.

        Args:
            source_obj: Source object (will be ignored)
            target_obj: Target object (will be kept)
            source_project: Source project
            target_project: Target project

        Returns:
            target_obj
        """
        logger.debug(f"Conflict resolved: target wins (GUID: {target_obj.Guid})")
        return target_obj


class NewestWinsResolver(ConflictResolver):
    """
    Resolve conflicts by choosing the most recently modified version.

    This strategy compares modification timestamps and chooses the newer version.
    Requires objects to have DateModified or similar timestamp properties.

    Use this when:
    - Both source and target are actively maintained
    - You want automatic conflict resolution based on recency
    - Bidirectional sync scenarios

    Example:
        >>> resolver = NewestWinsResolver()
        >>> sync.sync(
        ...     object_type="LexEntry",
        ...     conflict_resolver=resolver
        ... )

    Note:
        Full implementation in Phase 2. Phase 1 placeholder.
    """

    def resolve(self, source_obj: Any, target_obj: Any, source_project: Any, target_project: Any) -> Any:
        """
        Choose version with most recent modification date.

        Args:
            source_obj: Source object
            target_obj: Target object
            source_project: Source project
            target_project: Target project

        Returns:
            Newer object (source or target)
        """
        # Phase 1: Basic implementation
        # Full implementation with proper date comparison in Phase 2

        try:
            source_date = getattr(source_obj, "DateModified", None)
            target_date = getattr(target_obj, "DateModified", None)

            if source_date and target_date:
                if source_date > target_date:
                    logger.debug(f"Conflict resolved: source newer " f"({source_date} > {target_date})")
                    return source_obj
                else:
                    logger.debug(f"Conflict resolved: target newer " f"({target_date} >= {source_date})")
                    return target_obj

        except Exception as e:
            logger.warning(f"Could not compare dates: {e}")

        # Fallback to source wins
        logger.debug("Conflict resolved: fallback to source wins")
        return source_obj


class ManualResolver(ConflictResolver):
    """
    Resolve conflicts by prompting the user.

    This strategy asks the user to manually choose which version to keep
    for each conflict. Useful for interactive sync operations.

    Use this when:
    - Conflicts are rare and important
    - You want human review of changes
    - Data is critical and needs careful merging

    Example:
        >>> resolver = ManualResolver()
        >>> sync.sync(
        ...     object_type="LexEntry",
        ...     conflict_resolver=resolver
        ... )

    Note:
        Full implementation in Phase 2. Phase 1 placeholder.
    """

    def resolve(self, source_obj: Any, target_obj: Any, source_project: Any, target_project: Any) -> Any:
        """
        Prompt user to choose version.

        Args:
            source_obj: Source object
            target_obj: Target object
            source_project: Source project
            target_project: Target project

        Returns:
            User-chosen object

        Raises:
            NotImplementedError: Phase 1 - full implementation in Phase 2
        """
        # Phase 1: Not implemented
        # Full interactive UI in Phase 2
        raise NotImplementedError(
            "Manual conflict resolution not yet implemented (Phase 2). "
            "Use 'source_wins' or 'target_wins' for automated resolution."
        )


class FieldMergeResolver(ConflictResolver):
    """
    Resolve conflicts by merging specific fields.

    This strategy allows fine-grained control, merging some fields from source
    and keeping others from target.

    Example:
        >>> # Keep target's gloss, but update form from source
        >>> resolver = FieldMergeResolver(
        ...     source_fields=["form", "morph_type"],
        ...     target_fields=["gloss", "definition"]
        ... )

    Note:
        Full implementation in Phase 4. Phase 1 placeholder.
    """

    def __init__(self, source_fields: List[str], target_fields: List[str]):
        """
        Initialize FieldMergeResolver.

        Args:
            source_fields: Fields to take from source
            target_fields: Fields to keep from target
        """
        self.source_fields = source_fields
        self.target_fields = target_fields

    def resolve(self, source_obj: Any, target_obj: Any, source_project: Any, target_project: Any) -> Any:
        """
        Merge fields from both versions.

        Note:
            Phase 1 placeholder - full implementation in Phase 4.
        """
        raise NotImplementedError(
            "Field-level merge not yet implemented (Phase 4). "
            "Use 'source_wins' or 'target_wins' for whole-object resolution."
        )
