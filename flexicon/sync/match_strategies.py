"""
Match Strategies - Pluggable object matching strategies

This module provides strategies for matching objects between source and target projects.

Author: FlexTools Development Team
Date: 2025-11-26
"""

import logging
from typing import Any, Optional, List, Dict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class MatchStrategy(ABC):
    """
    Base class for object matching strategies.

    Match strategies determine how to match objects between source and target
    projects. Common strategies include GUID-based (for backups/forks) and
    field-based (for cross-project merging).

    Custom strategies can be implemented by sub classing and implementing match().
    """

    @abstractmethod
    def match(
        self, source_obj: Any, target_candidates: List[Any], source_project: Any, target_project: Any
    ) -> Optional[Any]:
        """
        Find matching target object for source object.

        Args:
            source_obj: Source object to match
            target_candidates: List of all target objects to search
            source_project: Source FLExProject instance
            target_project: Target FLExProject instance

        Returns:
            Matching target object, or None if no match found
        """
        pass


class GuidMatchStrategy(MatchStrategy):
    """
    Match objects by GUID (Globally Unique Identifier).

    This is the safest and most reliable matching strategy for projects that
    share a common history (backups, forks, branches). GUIDs are persistent
    across projects and never change.

    Use this strategy when:
    - Syncing between backup and main project
    - Syncing between test branch and stable branch
    - Source and target share common ancestry

    Example:
        >>> strategy = GuidMatchStrategy()
        >>> match = strategy.match(source_obj, target_objects, source_proj, target_proj)
    """

    def match(
        self, source_obj: Any, target_candidates: List[Any], source_project: Any, target_project: Any
    ) -> Optional[Any]:
        """
        Match by GUID.

        Args:
            source_obj: Source object with .Guid property
            target_candidates: Target objects to search
            source_project: Source project (unused)
            target_project: Target project (unused)

        Returns:
            Target object with matching GUID, or None
        """
        source_guid = str(source_obj.Guid)

        # Search for matching GUID in target
        for candidate in target_candidates:
            if str(candidate.Guid) == source_guid:
                logger.debug(f"Matched by GUID: {source_guid}")
                return candidate

        # No match found
        logger.debug(f"No GUID match for: {source_guid}")
        return None


class FieldMatchStrategy(MatchStrategy):
    """
    Match objects by field values.

    This strategy matches objects based on specified field values (e.g., headword,
    form, name). Useful for merging independent projects that don't share GUIDs.

    Use this strategy when:
    - Merging data from different projects
    - Source and target have no common history
    - Matching by semantic equivalence rather than identity

    Example:
        >>> # Match allomorphs by form
        >>> strategy = FieldMatchStrategy(
        ...     key_fields=["form"],
        ...     get_field_fn=lambda obj, ops: ops.GetForm(obj)
        ... )
        >>>
        >>> # Match entries by headword
        >>> strategy = FieldMatchStrategy(
        ...     key_fields=["headword"],
        ...     get_field_fn=lambda obj, ops: ops.GetHeadword(obj)
        ... )
    """

    def __init__(
        self,
        key_fields: List[str],
        get_field_fn: Optional[callable] = None,
        case_sensitive: bool = True,
        writing_system: Optional[str] = None,
    ):
        """
        Initialize FieldMatchStrategy.

        Args:
            key_fields: List of field names to match on
            get_field_fn: Optional custom function to extract field values
                         Signature: (obj, operations) -> field_value
            case_sensitive: Whether string comparison is case-sensitive
            writing_system: Optional writing system to use (default: vernacular)

        Example:
            >>> strategy = FieldMatchStrategy(
            ...     key_fields=["form", "morph_type"],
            ...     case_sensitive=False
            ... )
        """
        self.key_fields = key_fields
        self.get_field_fn = get_field_fn
        self.case_sensitive = case_sensitive
        self.writing_system = writing_system

    def match(
        self, source_obj: Any, target_candidates: List[Any], source_project: Any, target_project: Any
    ) -> Optional[Any]:
        """
        Match by field values.

        Args:
            source_obj: Source object
            target_candidates: Target objects to search
            source_project: Source project (for operations access)
            target_project: Target project (for operations access)

        Returns:
            First target object with matching field values, or None
        """
        # Get operations class name from source object
        ops_name = self._get_operations_name(source_obj)

        # Get operations instances
        source_ops = getattr(source_project, ops_name, None)
        target_ops = getattr(target_project, ops_name, None)

        if source_ops is None or target_ops is None:
            logger.warning(f"Could not get operations for {ops_name}")
            return None

        # Extract source field values
        source_values = self._extract_field_values(source_obj, source_ops)

        if source_values is None:
            return None

        # Search for matching target
        for candidate in target_candidates:
            target_values = self._extract_field_values(candidate, target_ops)

            if target_values is None:
                continue

            # Compare field values
            if self._values_match(source_values, target_values):
                logger.debug(f"Matched by fields {self.key_fields}: {source_values}")
                return candidate

        # No match found
        logger.debug(f"No field match for: {source_values}")
        return None

    def _get_operations_name(self, obj: Any) -> str:
        """Get operations class name for object."""
        # Get class name from object
        class_name = obj.ClassName

        # Common mappings
        mapping = {
            "MoStemAllomorph": "Allomorph",
            "LexEntry": "LexEntry",
            "LexSense": "LexSense",
            "LexExampleSentence": "Example",
            "PartOfSpeech": "POS",
            "PhPhoneme": "Phoneme",
            # Add more as needed
        }

        return mapping.get(class_name, class_name)

    def _extract_field_values(self, obj: Any, ops: Any) -> Optional[Dict[str, Any]]:
        """Extract field values from object."""
        values = {}

        for field in self.key_fields:
            value = self._get_field_value(obj, ops, field)
            if value is None:
                return None  # Required field missing
            values[field] = value

        return values

    def _get_field_value(self, obj: Any, ops: Any, field_name: str) -> Optional[Any]:
        """Get a single field value from object."""
        if self.get_field_fn:
            # Custom extraction function
            return self.get_field_fn(obj, ops)

        # Auto-detect based on field name
        if field_name == "form":
            if hasattr(ops, "GetForm"):
                return ops.GetForm(obj)

        elif field_name == "headword":
            if hasattr(ops, "GetHeadword"):
                return ops.GetHeadword(obj)

        elif field_name == "name":
            if hasattr(ops, "GetName"):
                return ops.GetName(obj)

        elif field_name == "gloss":
            if hasattr(ops, "GetGloss"):
                return ops.GetGloss(obj)

        # Fallback: try direct property access
        if hasattr(obj, field_name):
            return getattr(obj, field_name)

        logger.warning(f"Could not extract field '{field_name}' from {obj.ClassName}")
        return None

    def _values_match(self, source_values: Dict, target_values: Dict) -> bool:
        """Check if field values match."""
        for field in self.key_fields:
            source_val = source_values.get(field)
            target_val = target_values.get(field)

            if source_val is None or target_val is None:
                return False

            # String comparison
            if isinstance(source_val, str) and isinstance(target_val, str):
                if not self.case_sensitive:
                    source_val = source_val.lower()
                    target_val = target_val.lower()

                if source_val != target_val:
                    return False

            # Other types - direct comparison
            elif source_val != target_val:
                return False

        return True


class HybridMatchStrategy(MatchStrategy):
    """
    Hybrid matching: Try GUID first, fall back to field-based.

    This strategy combines GUID and field-based matching. It first attempts
    to match by GUID (fastest, most reliable), and if that fails, falls back
    to field-based matching.

    Use this strategy when:
    - Source and target may partially overlap
    - Some objects share GUIDs, others don't
    - You want reliability of GUID with flexibility of field matching

    Example:
        >>> strategy = HybridMatchStrategy(
        ...     fallback_fields=["headword"],
        ...     case_sensitive=False
        ... )
    """

    def __init__(self, fallback_fields: List[str], case_sensitive: bool = True):
        """
        Initialize HybridMatchStrategy.

        Args:
            fallback_fields: Fields to use for fallback field matching
            case_sensitive: Whether field matching is case-sensitive
        """
        self.guid_strategy = GuidMatchStrategy()
        self.field_strategy = FieldMatchStrategy(key_fields=fallback_fields, case_sensitive=case_sensitive)

    def match(
        self, source_obj: Any, target_candidates: List[Any], source_project: Any, target_project: Any
    ) -> Optional[Any]:
        """
        Try GUID match first, then field match.

        Args:
            source_obj: Source object
            target_candidates: Target objects
            source_project: Source project
            target_project: Target project

        Returns:
            Matched target object, or None
        """
        # Try GUID match first
        match = self.guid_strategy.match(source_obj, target_candidates, source_project, target_project)

        if match is not None:
            logger.debug("Matched by GUID (primary strategy)")
            return match

        # Fallback to field match
        match = self.field_strategy.match(source_obj, target_candidates, source_project, target_project)

        if match is not None:
            logger.debug("Matched by fields (fallback strategy)")

        return match
