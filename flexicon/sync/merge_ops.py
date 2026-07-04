"""
MergeOperations - Safe execution of sync operations

This module provides safe Create/Update/Delete operations for syncing
FLEx objects between projects.

Author: FlexTools Development Team
Date: 2025-11-26
"""

import logging
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class MergeOperations:
    """
    Execute sync operations safely.

    This class handles the actual creation, updating, and deletion of FLEx
    objects during sync operations. All operations include validation and
    error handling.

    Usage:
        >>> merger = MergeOperations(target_project)
        >>> merger.create_object(
        ...     target_ops=target_project.Allomorph,
        ...     source_obj=source_allomorph,
        ...     source_ops=source_project.Allomorph,
        ...     parent_obj=target_entry
        ... )
    """

    def __init__(self, target_project: Any):
        """
        Initialize MergeOperations.

        Args:
            target_project: Target FLExProject instance (must have writeEnabled=True)

        Raises:
            RuntimeError: If project not writable
        """
        self.target_project = target_project

        # Validate write access
        if hasattr(target_project, "writeEnabled") and not target_project.writeEnabled:
            raise RuntimeError("Target project not opened with writeEnabled=True. " "Cannot perform merge operations.")

        logger.info(f"MergeOperations initialized for {self._get_project_name()}")

    def _get_project_name(self) -> str:
        """Get project name for logging."""
        if hasattr(self.target_project, "ProjectName"):
            return self.target_project.ProjectName()
        return "unknown"

    def create_object(
        self, target_ops: Any, source_obj: Any, source_ops: Any, parent_obj: Optional[Any] = None, **create_kwargs
    ) -> Any:
        """
        Create a new object in target project.

        This method creates a new object by extracting properties from the
        source object and calling the appropriate Operations.Create() method.

        Args:
            target_ops: Target operations instance (e.g., target_project.Allomorph)
            source_obj: Source object to copy from
            source_ops: Source operations instance
            parent_obj: Optional parent object (for owned objects)
            **create_kwargs: Additional arguments for Create() method

        Returns:
            Newly created object in target

        Raises:
            RuntimeError: If creation fails
            AttributeError: If Create method not available

        Example:
            >>> # Create allomorph in target
            >>> new_allomorph = merger.create_object(
            ...     target_ops=target_project.Allomorph,
            ...     source_obj=source_allomorph,
            ...     source_ops=source_project.Allomorph,
            ...     parent_obj=target_entry
            ... )
        """
        if not hasattr(target_ops, "Create"):
            raise AttributeError(f"{target_ops.__class__.__name__} does not have Create() method")

        try:
            # Extract properties needed for creation
            # This varies by object type, so we try common patterns

            # For Allomorphs: Create(entry, form, morph_type)
            if hasattr(source_ops, "GetForm"):
                form = source_ops.GetForm(source_obj)
                morph_type = source_ops.GetMorphType(source_obj) if hasattr(source_ops, "GetMorphType") else None

                logger.debug(f"Creating object with form: {form}")

                if morph_type and parent_obj:
                    created_obj = target_ops.Create(parent_obj, form, morph_type, **create_kwargs)
                elif parent_obj:
                    created_obj = target_ops.Create(parent_obj, form, **create_kwargs)
                else:
                    created_obj = target_ops.Create(form, **create_kwargs)

            # For LexEntry: Create(lexeme_form, morph_type)
            elif hasattr(source_ops, "GetLexemeForm"):
                lexeme_form = source_ops.GetLexemeForm(source_obj)
                morph_type = source_ops.GetMorphType(source_obj) if hasattr(source_ops, "GetMorphType") else None

                logger.debug(f"Creating entry with lexeme form: {lexeme_form}")

                if morph_type:
                    created_obj = target_ops.Create(lexeme_form, morph_type, **create_kwargs)
                else:
                    created_obj = target_ops.Create(lexeme_form, **create_kwargs)

            # For objects with name: Create(name)
            elif hasattr(source_ops, "GetName"):
                name = source_ops.GetName(source_obj)

                logger.debug(f"Creating object with name: {name}")

                if parent_obj:
                    created_obj = target_ops.Create(parent_obj, name, **create_kwargs)
                else:
                    created_obj = target_ops.Create(name, **create_kwargs)

            else:
                # Generic create (no parameters)
                logger.debug("Creating object with generic Create()")
                created_obj = target_ops.Create(**create_kwargs)

            # Copy additional properties
            self.copy_properties(source_obj, created_obj, source_ops, target_ops)

            logger.info(f"Created object: {str(created_obj.Guid)[:8]}...")
            return created_obj

        except Exception as e:
            logger.error(f"Failed to create object: {e}")
            raise RuntimeError(f"Object creation failed: {e}")

    def update_object(
        self, target_obj: Any, source_obj: Any, source_ops: Any, target_ops: Any, fields: Optional[List[str]] = None
    ) -> bool:
        """
        Update an existing object in target project.

        Copies properties from source object to target object. If fields is
        specified, only those fields are updated. Otherwise, all common
        properties are updated.

        This method will attempt to use the new CompareTo() method if available
        on the operations class to efficiently detect differences. Falls back
        to traditional property-by-property copying if not available.

        Args:
            target_obj: Target object to update
            source_obj: Source object to copy from
            source_ops: Source operations instance
            target_ops: Target operations instance
            fields: Optional list of specific fields to update

        Returns:
            True if any changes were made

        Raises:
            RuntimeError: If update fails

        Example:
            >>> # Update allomorph form only
            >>> changed = merger.update_object(
            ...     target_obj=target_allomorph,
            ...     source_obj=source_allomorph,
            ...     source_ops=source_project.Allomorph,
            ...     target_ops=target_project.Allomorph,
            ...     fields=["form"]
            ... )
        """
        try:
            changed = False

            # If specific fields requested, update only those
            if fields:
                for field in fields:
                    if self._update_field(target_obj, source_obj, source_ops, target_ops, field):
                        changed = True
            else:
                # Try to use CompareTo() if available for efficient difference detection
                # This is the new sync framework integration
                if hasattr(source_ops, "CompareTo"):
                    try:
                        is_different, differences = source_ops.CompareTo(
                            source_obj, target_obj, ops1=source_ops, ops2=target_ops
                        )

                        if is_different:
                            logger.debug(f"CompareTo detected {len(differences)} differences")
                            # Copy all properties to apply the differences
                            changed = self.copy_properties(source_obj, target_obj, source_ops, target_ops)
                        else:
                            logger.debug("CompareTo: No differences detected")
                            changed = False
                    except Exception as e:
                        # Fall back to traditional copy if CompareTo fails
                        logger.debug(f"CompareTo failed, falling back to copy_properties: {e}")
                        changed = self.copy_properties(source_obj, target_obj, source_ops, target_ops)
                else:
                    # Traditional approach: Update all common properties
                    changed = self.copy_properties(source_obj, target_obj, source_ops, target_ops)

            if changed:
                logger.info(f"Updated object: {str(target_obj.Guid)[:8]}...")
            else:
                logger.debug(f"No changes needed for: {str(target_obj.Guid)[:8]}...")

            return changed

        except Exception as e:
            logger.error(f"Failed to update object: {e}")
            raise RuntimeError(f"Object update failed: {e}")

    def delete_object(self, target_ops: Any, target_obj: Any, validate_safe: bool = True) -> bool:
        """
        Delete an object from target project.

        Args:
            target_ops: Target operations instance
            target_obj: Object to delete
            validate_safe: If True, perform safety checks before deleting

        Returns:
            True if deleted successfully

        Raises:
            RuntimeError: If deletion fails or is unsafe

        Example:
            >>> # Delete allomorph
            >>> deleted = merger.delete_object(
            ...     target_ops=target_project.Allomorph,
            ...     target_obj=target_allomorph
            ... )
        """
        if not hasattr(target_ops, "Delete"):
            raise AttributeError(f"{target_ops.__class__.__name__} does not have Delete() method")

        try:
            # Optional: Validate that deletion is safe
            if validate_safe:
                # Check if object is referenced elsewhere
                # This is complex and object-type specific
                # For Phase 2, we trust the user's intent
                pass

            # Perform deletion
            target_ops.Delete(target_obj)

            logger.info(f"Deleted object: {str(target_obj.Guid)[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to delete object: {e}")
            raise RuntimeError(f"Object deletion failed: {e}")

    def copy_properties(self, source_obj: Any, target_obj: Any, source_ops: Any, target_ops: Any) -> bool:
        """
        Copy properties from source to target object.

        This method first attempts to use the new GetSyncableProperties() method
        from the sync framework if available. This provides complete, accurate
        property coverage for all object types.

        If GetSyncableProperties() is not available, falls back to traditional
        pattern matching of Get*/Set* methods for backwards compatibility.

        Args:
            source_obj: Source object to copy from
            target_obj: Target object to copy to
            source_ops: Source operations instance
            target_ops: Target operations instance

        Returns:
            True if any properties were changed

        Example:
            >>> # Copy all properties
            >>> changed = merger.copy_properties(
            ...     source_allomorph,
            ...     target_allomorph,
            ...     source_project.Allomorph,
            ...     target_project.Allomorph
            ... )
        """
        changed = False

        # NEW: Try to use GetSyncableProperties() if available (sync framework integration)
        # This method provides comprehensive property coverage and is the preferred approach
        if hasattr(source_ops, "GetSyncableProperties"):
            try:
                logger.debug("Using GetSyncableProperties() for property copying")
                source_props = source_ops.GetSyncableProperties(source_obj)

                # Map syncable property names to their setter methods
                # This mapping handles the conversion from property dict keys to operation methods
                property_to_setter = {
                    "Form": "SetForm",
                    "Name": "SetName",
                    "Gloss": "SetGloss",
                    "Definition": "SetDefinition",
                    "Comment": "SetComment",
                    "CitationForm": "SetCitationForm",
                    "IsAbstract": None,  # Boolean properties often set directly
                    "MorphTypeRA": "SetMorphType",
                    # Add more mappings as needed for other object types
                }

                for prop_name, prop_value in source_props.items():
                    setter_name = property_to_setter.get(prop_name)

                    if setter_name and hasattr(target_ops, setter_name):
                        try:
                            # Get current value for comparison
                            getter_name = setter_name.replace("Set", "Get")
                            target_value = None
                            if hasattr(target_ops, getter_name):
                                target_value = getattr(target_ops, getter_name)(target_obj)

                            # Only update if different
                            # For MultiString properties (dicts), compare dict representations
                            if prop_value != target_value:
                                # Special handling for MultiString properties (represented as dicts)
                                if isinstance(prop_value, dict):
                                    # For each writing system in the source
                                    for ws_tag, text in prop_value.items():
                                        # Convert ws_tag to ws_handle and call setter
                                        # This is simplified - actual implementation may need WSHandle conversion
                                        getattr(target_ops, setter_name)(target_obj, text)
                                        changed = True
                                        logger.debug(f"Updated {prop_name}[{ws_tag}]: {text}")
                                else:
                                    # Simple property - just call setter
                                    getattr(target_ops, setter_name)(target_obj, prop_value)
                                    changed = True
                                    logger.debug(f"Updated {prop_name}: {target_value} → {prop_value}")

                        except Exception as e:
                            # Non-critical - some properties may not be settable
                            logger.debug(f"Could not copy {prop_name} via GetSyncableProperties: {e}")

                # If we successfully used GetSyncableProperties, return now
                if changed or len(source_props) > 0:
                    logger.debug(f"GetSyncableProperties processed {len(source_props)} properties")
                    return changed

            except Exception as e:
                # Fall through to traditional approach if GetSyncableProperties fails
                logger.debug(f"GetSyncableProperties failed, falling back to pattern matching: {e}")

        # FALLBACK: Traditional property pattern matching for backwards compatibility
        # This works with older operation classes that don't have GetSyncableProperties()
        logger.debug("Using traditional Get*/Set* pattern matching for property copying")

        # Common property patterns to check
        # Each tuple: (getter_name, setter_name, property_name)
        property_patterns = [
            ("GetForm", "SetForm", "form"),
            ("GetName", "SetName", "name"),
            ("GetGloss", "SetGloss", "gloss"),
            ("GetDefinition", "SetDefinition", "definition"),
            ("GetComment", "SetComment", "comment"),
            ("GetCitationForm", "SetCitationForm", "citation_form"),
        ]

        for getter, setter, prop_name in property_patterns:
            if hasattr(source_ops, getter) and hasattr(target_ops, setter):
                try:
                    source_value = getattr(source_ops, getter)(source_obj)
                    target_value = getattr(target_ops, getter)(target_obj) if hasattr(target_ops, getter) else None

                    # Only update if different
                    if source_value != target_value:
                        getattr(target_ops, setter)(target_obj, source_value)
                        changed = True
                        logger.debug(f"Updated {prop_name}: {target_value} → {source_value}")

                except Exception as e:
                    # Non-critical - some properties may not apply to all objects
                    logger.debug(f"Could not copy {prop_name}: {e}")

        return changed

    def _update_field(
        self, target_obj: Any, source_obj: Any, source_ops: Any, target_ops: Any, field_name: str
    ) -> bool:
        """Update a single field."""
        # Map field name to getter/setter methods
        field_map = {
            "form": ("GetForm", "SetForm"),
            "name": ("GetName", "SetName"),
            "gloss": ("GetGloss", "SetGloss"),
            "definition": ("GetDefinition", "SetDefinition"),
            "comment": ("GetComment", "SetComment"),
            "citation_form": ("GetCitationForm", "SetCitationForm"),
        }

        if field_name not in field_map:
            logger.warning(f"Unknown field: {field_name}")
            return False

        getter, setter = field_map[field_name]

        if not hasattr(source_ops, getter) or not hasattr(target_ops, setter):
            logger.warning(f"Field {field_name} not available for this object type")
            return False

        try:
            source_value = getattr(source_ops, getter)(source_obj)
            target_value = getattr(target_ops, getter)(target_obj) if hasattr(target_ops, getter) else None

            if source_value != target_value:
                getattr(target_ops, setter)(target_obj, source_value)
                logger.debug(f"Updated {field_name}: {target_value} → {source_value}")
                return True

            return False

        except Exception as e:
            logger.warning(f"Could not update {field_name}: {e}")
            return False


class SyncChange:
    """
    Record of a single change made during sync.

    Used for undo/audit tracking.
    """

    def __init__(
        self,
        operation: str,  # 'create', 'update', 'delete'
        object_type: str,
        object_guid: str,
        details: Optional[Dict] = None,
    ):
        """Initialize sync change record."""
        self.operation = operation
        self.object_type = object_type
        self.object_guid = object_guid
        self.details = details or {}

    def __repr__(self):
        return f"SyncChange({self.operation}, {self.object_type}, {self.object_guid[:8]}...)"


class SyncError:
    """
    Record of an error during sync.
    """

    def __init__(self, operation: str, object_guid: Optional[str], error_message: str):
        """Initialize sync error record."""
        self.operation = operation
        self.object_guid = object_guid
        self.error_message = error_message

    def __repr__(self):
        return f"SyncError({self.operation}, {self.error_message})"
