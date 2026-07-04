"""
Selective Import Operations

One-way import of specific objects from source to target project.
Matches the actual linguistic workflow: "import new allomorphs to stable project".

Author: FlexTools Development Team
Date: 2025-11-27
"""

import logging
from typing import Any, List, Optional, Callable
from datetime import datetime
from .validation import LinguisticValidator, ValidationError, ValidationResult
from .merge_ops import MergeOperations, SyncChange, SyncError
from .engine import SyncResult

logger = logging.getLogger(__name__)


class SelectiveImport:
    """
    One-way selective import from source to target project.

    This matches the linguist's actual workflow:
    1. Copy project for testing
    2. Make changes in test project
    3. Import ONLY new/modified items back to stable project
    4. NEVER overwrite stable project's existing data

    Usage:
        >>> importer = SelectiveImport(source_project, target_project)
        >>> result = importer.import_new_objects(
        ...     object_type="Allomorph",
        ...     created_after=backup_timestamp,
        ...     validate_references=True
        ... )
        >>> print(result.summary())

    This is SAFER than bidirectional sync for linguistic data.
    """

    def __init__(self, source_project: Any, target_project: Any):
        """
        Initialize selective importer.

        Args:
            source_project: Source FLEx project (test/backup)
            target_project: Target FLEx project (stable/main)

        Raises:
            RuntimeError: If target not write-enabled
        """
        self.source_project = source_project
        self.target_project = target_project

        # Validate write access
        if hasattr(target_project, "writeEnabled") and not target_project.writeEnabled:
            raise RuntimeError("Target project not opened with writeEnabled=True. " "Cannot perform import operations.")

        self.validator = LinguisticValidator(target_project)
        self.merger = MergeOperations(target_project)

        logger.info(
            f"SelectiveImport initialized: {self._get_project_name(source_project)} → {self._get_project_name(target_project)}"
        )

    def import_new_objects(
        self,
        object_type: str,
        created_after: Optional[datetime] = None,
        modified_after: Optional[datetime] = None,
        validate_references: bool = True,
        include_owned: bool = False,
        progress_callback: Optional[Callable[[str], None]] = None,
        dry_run: bool = False,
    ) -> SyncResult:
        """
        Import objects created/modified after specified date.

        This is the PRIMARY method for linguistic workflows:
        - Imports NEW objects only (not in target)
        - Filters by creation/modification date
        - NEVER overwrites existing target data
        - One-way operation (source → target only)

        Args:
            object_type: Type to import (e.g., "Allomorph", "LexEntry")
            created_after: Only import objects created after this time
            modified_after: Only import objects modified after this time
            validate_references: Check for missing references before import
            include_owned: Also import owned objects (WARNING: complex)
            progress_callback: Optional progress updates
            dry_run: Preview without making changes

        Returns:
            SyncResult with import statistics

        Example:
            >>> # User workflow: backup → test → import new
            >>> backup_time = datetime(2025, 11, 1)
            >>> # ... work in test project ...
            >>> result = importer.import_new_objects(
            ...     object_type="Allomorph",
            ...     created_after=backup_time,
            ...     validate_references=True
            ... )
            >>> print(f"Imported {result.num_created} new allomorphs")
        """
        result = SyncResult(object_type)

        try:
            # Get operations classes
            source_ops = self._get_operations(self.source_project, object_type)
            target_ops = self._get_operations(self.target_project, object_type)

            if progress_callback:
                progress_callback(f"Scanning {object_type} objects in source...")

            # Get all objects from source
            source_objects = source_ops.GetAll()

            # Filter by date
            candidates = []
            for obj in source_objects:
                # Check if already exists in target
                guid = str(obj.Guid)
                if self._exists_in_target(guid):
                    continue  # Skip existing - NEVER overwrite

                # Check creation date
                if created_after and hasattr(obj, "DateCreated"):
                    if obj.DateCreated < created_after:
                        continue

                # Check modification date
                if modified_after and hasattr(obj, "DateModified"):
                    if obj.DateModified < modified_after:
                        continue

                candidates.append(obj)

            if progress_callback:
                progress_callback(f"Found {len(candidates)} new objects to import")

            # Validate candidates
            if validate_references:
                if progress_callback:
                    progress_callback("Validating references...")

                validation_issues = []
                for obj in candidates:
                    validation = self.validator.validate_before_create(obj, self.source_project, object_type)
                    if validation.has_critical:
                        validation_issues.append((obj, validation))

                if validation_issues:
                    # Log all issues
                    for obj, validation in validation_issues:
                        guid = str(obj.Guid)
                        logger.warning(f"Validation failed for {guid}:")
                        logger.warning(validation.detailed_report())

                        result.add_error(
                            SyncError(
                                operation="validate",
                                object_guid=guid,
                                error_message=f"Validation failed: {validation.num_critical} critical issues",
                            )
                        )

                    if not dry_run:
                        # Create consolidated validation result for error
                        consolidated = ValidationResult()
                        for obj, validation in validation_issues:
                            for issue in validation.issues:
                                consolidated.add_issue(issue)
                        raise ValidationError(consolidated)

            # Import objects
            imported = 0
            for obj in candidates:
                guid = str(obj.Guid)

                try:
                    if not dry_run:
                        # Create object in target
                        created_obj = self.merger.create_object(
                            target_ops=target_ops, source_obj=obj, source_ops=source_ops
                        )

                        if created_obj:
                            result.add_change(SyncChange(operation="create", object_type=object_type, object_guid=guid))
                            imported += 1

                            if progress_callback and imported % 10 == 0:
                                progress_callback(f"Imported {imported}/{len(candidates)}")
                        else:
                            result.add_error(
                                SyncError(
                                    operation="create", object_guid=guid, error_message="create_object returned None"
                                )
                            )
                    else:
                        # Dry run - just count
                        result.skip()

                except Exception as e:
                    logger.error(f"Failed to import {guid}: {e}")
                    result.add_error(SyncError(operation="create", object_guid=guid, error_message=str(e)))

            if progress_callback:
                if dry_run:
                    progress_callback(f"Dry run: Would import {len(candidates)} objects")
                else:
                    progress_callback(f"Import complete: {imported} objects created")

        except ValidationError:
            # Re-raise validation errors - they should propagate
            raise
        except Exception as e:
            logger.error(f"Import failed: {e}")
            result.add_error(SyncError(operation="import", object_guid=None, error_message=str(e)))

        return result

    def import_by_filter(
        self,
        object_type: str,
        filter_fn: Callable[[Any], bool],
        validate_references: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
        dry_run: bool = False,
    ) -> SyncResult:
        """
        Import objects matching custom filter function.

        Args:
            object_type: Type to import
            filter_fn: Function that returns True for objects to import
            validate_references: Validate before import
            progress_callback: Progress updates
            dry_run: Preview mode

        Returns:
            SyncResult with statistics

        Example:
            >>> # Import only verified allomorphs
            >>> def is_verified(obj):
            ...     return hasattr(obj, 'Status') and obj.Status == 'Verified'
            >>> result = importer.import_by_filter(
            ...     object_type="Allomorph",
            ...     filter_fn=is_verified
            ... )
        """
        result = SyncResult(object_type)

        try:
            source_ops = self._get_operations(self.source_project, object_type)
            target_ops = self._get_operations(self.target_project, object_type)

            if progress_callback:
                progress_callback("Scanning source objects...")

            # Get all source objects
            source_objects = source_ops.GetAll()

            # Filter objects
            candidates = []
            for obj in source_objects:
                # Skip if exists in target
                guid = str(obj.Guid)
                if self._exists_in_target(guid):
                    continue

                # Apply custom filter
                try:
                    if filter_fn(obj):
                        candidates.append(obj)
                except Exception as e:
                    logger.warning(f"Filter function failed for {guid}: {e}")

            if progress_callback:
                progress_callback(f"Found {len(candidates)} objects matching filter")

            # Use same import logic as import_new_objects
            # (validation and creation)
            for obj in candidates:
                guid = str(obj.Guid)

                try:
                    if validate_references:
                        validation = self.validator.validate_before_create(obj, self.source_project, object_type)
                        if validation.has_critical:
                            result.add_error(
                                SyncError(
                                    operation="validate",
                                    object_guid=guid,
                                    error_message=f"{validation.num_critical} validation errors",
                                )
                            )
                            continue

                    if not dry_run:
                        created_obj = self.merger.create_object(
                            target_ops=target_ops, source_obj=obj, source_ops=source_ops
                        )

                        if created_obj:
                            result.add_change(SyncChange(operation="create", object_type=object_type, object_guid=guid))
                        else:
                            result.add_error(
                                SyncError(operation="create", object_guid=guid, error_message="Creation failed")
                            )
                    else:
                        result.skip()

                except Exception as e:
                    logger.error(f"Failed to import {guid}: {e}")
                    result.add_error(SyncError(operation="create", object_guid=guid, error_message=str(e)))

        except ValidationError:
            # Re-raise validation errors - they should propagate
            raise
        except Exception as e:
            logger.error(f"Import failed: {e}")
            result.add_error(SyncError(operation="import", object_guid=None, error_message=str(e)))

        return result

    def _get_operations(self, project: Any, object_type: str) -> Any:
        """Get operations class for object type."""
        if not hasattr(project, object_type):
            raise AttributeError(
                f"Project does not have operations class for '{object_type}'. " f"Available: {dir(project)}"
            )
        return getattr(project, object_type)

    def _exists_in_target(self, guid: str) -> bool:
        """Check if object exists in target project."""
        try:
            obj = self.target_project.Object(guid)
            return obj is not None
        except (AttributeError, KeyError):
            return False

    def _get_project_name(self, project: Any) -> str:
        """Get project name for logging."""
        if hasattr(project, "ProjectName"):
            return project.ProjectName()
        return "unknown"
