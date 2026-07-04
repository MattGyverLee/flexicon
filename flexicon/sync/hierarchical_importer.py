"""
Hierarchical Importer - Phase 3.3

Import FLEx objects with full dependency resolution and hierarchical cascade.

Author: FlexTools Development Team
Date: 2025-11-27
"""

import logging
from typing import Any, List, Optional, Callable
from datetime import datetime

from .dependency_graph import DependencyGraph, CircularDependencyError
from .dependency_resolver import DependencyResolver, DependencyConfig
from .validation import LinguisticValidator, ValidationError, ValidationResult
from .merge_ops import MergeOperations, SyncError
from .engine import SyncResult

logger = logging.getLogger(__name__)


class HierarchicalImporter:
    """
    Import FLEx objects with dependency resolution.

    Automatically discovers and imports all required dependencies,
    including owned objects (senses, examples) and referenced objects
    (POS, semantic domains).
    """

    def __init__(self, source_project: Any, target_project: Any):
        """
        Initialize hierarchical importer.

        Args:
            source_project: Source FlexProject
            target_project: Target FlexProject (must be writeEnabled)
        """
        self.source_project = source_project
        self.target_project = target_project

        # Check write access
        if hasattr(target_project, "writeEnabled") and not target_project.writeEnabled:
            raise RuntimeError("Target project must be opened with writeEnabled=True for import operations")

        # Initialize components
        self.resolver = DependencyResolver(source_project, target_project)
        self.validator = LinguisticValidator(target_project)
        self.merger = MergeOperations(source_project, target_project)

    def import_with_dependencies(
        self,
        object_type: str,
        guids: List[str],
        config: Optional[DependencyConfig] = None,
        validate_references: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
        dry_run: bool = False,
    ) -> SyncResult:
        """
        Import objects with full dependency trees.

        Discovers all dependencies (owned objects, referenced objects)
        and imports them in correct order.

        Args:
            object_type: Type of root objects to import
            guids: List of GUIDs to import
            config: Dependency resolution configuration
            validate_references: Validate all objects before import
            progress_callback: Optional callback for progress updates
            dry_run: If True, preview without actually importing

        Returns:
            SyncResult with import details

        Raises:
            CircularDependencyError: If circular dependency detected
            ValidationError: If validation fails with critical issues
        """
        result = SyncResult(object_type)

        if config is None:
            config = DependencyConfig()

        try:
            if progress_callback:
                progress_callback(f"Resolving dependencies for {len(guids)} {object_type} object(s)...")

            # Build dependency graph
            graph = DependencyGraph()

            for guid in guids:
                # Get object from source
                obj = self._get_operations(self.source_project, object_type).Object(guid)
                if obj is None:
                    logger.warning(f"Object {guid} not found in source project")
                    result.add_error(
                        SyncError(
                            operation="resolve",
                            object_guid=guid,
                            error_message=f"{object_type} not found in source project",
                        )
                    )
                    continue

                # Resolve dependencies
                obj_graph = self.resolver.resolve_dependencies(obj, object_type, config)

                # Merge into main graph
                self._merge_graphs(graph, obj_graph)

            if progress_callback:
                progress_callback(f"Dependency graph: {len(graph)} objects")
                logger.info(graph.summary())

            # Detect cycles
            cycles = graph.detect_cycles()
            if cycles and not config.allow_cycles:
                raise CircularDependencyError(cycles[0])

            # Get import order
            try:
                import_order = graph.get_import_order()
            except CircularDependencyError:
                # Try to break cycles at weak links (cross-references)
                if config.allow_cycles:
                    import_order = self._break_cycles_and_sort(graph)
                else:
                    raise

            if progress_callback:
                progress_callback(f"Import order determined: {len(import_order)} objects")

            # Validate all objects
            if validate_references and config.validate_all:
                validation_issues = self._validate_all(graph, import_order, progress_callback)

                if validation_issues and not dry_run:
                    # Consolidate validation results
                    consolidated = ValidationResult()
                    for validation in validation_issues:
                        for issue in validation.issues:
                            consolidated.add_issue(issue)

                    raise ValidationError(consolidated)

            # Import objects in order
            imported_count = self._import_objects(
                graph=graph,
                import_order=import_order,
                result=result,
                progress_callback=progress_callback,
                dry_run=dry_run,
            )

            if progress_callback:
                if dry_run:
                    progress_callback(f"Dry run complete: Would import {imported_count} objects")
                else:
                    progress_callback(f"Import complete: {imported_count} objects created")

        except ValidationError:
            # Re-raise validation errors
            raise
        except CircularDependencyError:
            # Re-raise circular dependency errors
            raise
        except Exception as e:
            logger.error(f"Import failed: {e}")
            result.add_error(SyncError(operation="import", object_guid=None, error_message=str(e)))

        return result

    def import_related(
        self,
        object_type: str,
        guid: str,
        include_referring_objects: Optional[List[str]] = None,
        validate_references: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
        dry_run: bool = False,
    ) -> SyncResult:
        """
        Import object and all objects that refer to it.

        Useful for importing a semantic domain with all entries that use it,
        or a POS with all senses that reference it.

        Args:
            object_type: Type of object to import
            guid: GUID of object
            include_referring_objects: List of object types to import if they refer to this
            validate_references: Validate all objects
            progress_callback: Optional callback for progress updates
            dry_run: If True, preview without importing

        Returns:
            SyncResult with import details
        """
        result = SyncResult(object_type)

        try:
            if progress_callback:
                progress_callback(f"Finding objects that reference {guid}...")

            # Get the main object
            ops = self._get_operations(self.source_project, object_type)
            obj = ops.Object(guid)

            if obj is None:
                result.add_error(
                    SyncError(
                        operation="resolve",
                        object_guid=guid,
                        error_message=f"{object_type} not found in source project",
                    )
                )
                return result

            # Start with importing the main object
            config = DependencyConfig(include_owned=False, resolve_references=True)
            graph = self.resolver.resolve_dependencies(obj, object_type, config)

            # Find objects that reference this one
            if include_referring_objects:
                for ref_type in include_referring_objects:
                    referring_objs = self._find_referring_objects(guid, ref_type)

                    if progress_callback:
                        progress_callback(f"Found {len(referring_objs)} {ref_type} objects")

                    for ref_obj in referring_objs:
                        ref_guid = str(ref_obj.Guid)

                        # Resolve dependencies for referring object
                        ref_config = DependencyConfig(include_owned=True, resolve_references=True)
                        ref_graph = self.resolver.resolve_dependencies(ref_obj, ref_type, ref_config)

                        # Merge graphs
                        self._merge_graphs(graph, ref_graph)

            if progress_callback:
                progress_callback(f"Dependency graph: {len(graph)} objects")

            # Get import order
            import_order = graph.get_import_order()

            # Import objects
            imported_count = self._import_objects(
                graph=graph,
                import_order=import_order,
                result=result,
                progress_callback=progress_callback,
                dry_run=dry_run,
            )

            if progress_callback:
                if dry_run:
                    progress_callback(f"Dry run: Would import {imported_count} objects")
                else:
                    progress_callback(f"Imported {imported_count} objects")

        except Exception as e:
            logger.error(f"Import failed: {e}")
            result.add_error(SyncError(operation="import", object_guid=None, error_message=str(e)))

        return result

    def _import_objects(
        self,
        graph: DependencyGraph,
        import_order: List[tuple],
        result: SyncResult,
        progress_callback: Optional[Callable[[str], None]],
        dry_run: bool,
    ) -> int:
        """Import objects in dependency order."""
        imported_count = 0
        total = len(import_order)

        for idx, (guid, obj_type) in enumerate(import_order):
            # Check if already exists
            if self._exists_in_target(guid):
                logger.debug(f"Object {guid} already exists, skipping")
                continue

            # Get object
            node = graph.nodes.get(guid)
            if node is None or node.obj is None:
                # Object not available (might be a reference that exists in target)
                continue

            # Progress update
            if progress_callback and (idx % 10 == 0 or idx == total - 1):
                progress_callback(f"Processing {idx + 1}/{total}: {obj_type}")

            if dry_run:
                # Just count
                result.skip()
                imported_count += 1
            else:
                # Actually import
                try:
                    target_ops = self._get_operations(self.target_project, obj_type)
                    source_ops = self._get_operations(self.source_project, obj_type)

                    created_obj = self.merger.create_object(
                        target_ops=target_ops, source_obj=node.obj, source_ops=source_ops
                    )

                    if created_obj:
                        from .merge_ops import SyncChange

                        result.add_change(SyncChange(operation="create", object_type=obj_type, object_guid=guid))
                        imported_count += 1
                    else:
                        result.add_error(
                            SyncError(operation="create", object_guid=guid, error_message="create_object returned None")
                        )

                except Exception as e:
                    logger.error(f"Failed to import {guid}: {e}")
                    result.add_error(SyncError(operation="create", object_guid=guid, error_message=str(e)))

        return imported_count

    def _validate_all(
        self, graph: DependencyGraph, import_order: List[tuple], progress_callback: Optional[Callable[[str], None]]
    ) -> List[ValidationResult]:
        """Validate all objects in import order."""
        validation_issues = []

        for idx, (guid, obj_type) in enumerate(import_order):
            node = graph.nodes.get(guid)
            if node is None or node.obj is None:
                continue

            # Validate
            validation = self.validator.validate_before_create(node.obj, self.source_project, obj_type)

            if validation.has_critical:
                validation_issues.append(validation)
                logger.warning(f"Validation failed for {guid}:")
                logger.warning(validation.detailed_report())

        if validation_issues and progress_callback:
            progress_callback(f"Validation found {len(validation_issues)} objects with critical issues")

        return validation_issues

    def _merge_graphs(self, target: DependencyGraph, source: DependencyGraph):
        """Merge source graph into target graph."""
        # Add all nodes
        for guid, node in source.nodes.items():
            if guid not in target:
                target.add_object(guid, node.object_type, node.obj)

        # Add all dependencies
        for guid, node in source.nodes.items():
            for dep_guid in node.dependencies:
                dep_type = node.dependency_types[dep_guid]
                target.add_dependency(guid, dep_guid, dep_type)

    def _break_cycles_and_sort(self, graph: DependencyGraph) -> List[tuple]:
        """Break cycles at weakest links and return topological sort."""
        from .dependency_graph import DependencyType

        # Find all cycles
        cycles = graph.detect_cycles()

        while cycles:
            # Break the first cycle at a CROSS_REFERENCE link (weakest)
            cycle = cycles[0]

            # Find a cross-reference link to break
            broken = False
            for i in range(len(cycle) - 1):
                from_guid = cycle[i]
                to_guid = cycle[i + 1]

                if from_guid in graph.nodes:
                    node = graph.nodes[from_guid]
                    if to_guid in node.dependency_types:
                        dep_type = node.dependency_types[to_guid]
                        if dep_type == DependencyType.CROSS_REFERENCE:
                            # Break this link
                            graph.remove_dependency(from_guid, to_guid)
                            logger.info(f"Broke cycle at {from_guid} → {to_guid}")
                            broken = True
                            break

            if not broken:
                # No cross-reference found, break at any REFERENCE
                for i in range(len(cycle) - 1):
                    from_guid = cycle[i]
                    to_guid = cycle[i + 1]

                    if from_guid in graph.nodes:
                        node = graph.nodes[from_guid]
                        if to_guid in node.dependency_types:
                            dep_type = node.dependency_types[to_guid]
                            if dep_type == DependencyType.REFERENCE:
                                graph.remove_dependency(from_guid, to_guid)
                                logger.info(f"Broke cycle at {from_guid} → {to_guid}")
                                broken = True
                                break

            if not broken:
                # Last resort: break first link
                graph.remove_dependency(cycle[0], cycle[1])
                logger.warning(f"Broke cycle at ownership link {cycle[0]} → {cycle[1]}")

            # Re-detect cycles
            cycles = graph.detect_cycles()

        # Now get topological sort
        return graph.get_import_order()

    def _find_referring_objects(self, guid: str, object_type: str) -> List[Any]:
        """Find all objects of given type that reference the specified object."""
        referring = []

        try:
            ops = self._get_operations(self.source_project, object_type)
            all_objects = ops.GetAll()

            for obj in all_objects:
                # Check if this object references the target GUID
                if self._object_references(obj, guid, object_type):
                    referring.append(obj)

        except Exception as e:
            logger.error(f"Error finding referring objects: {e}")

        return referring

    def _object_references(self, obj: Any, target_guid: str, object_type: str) -> bool:
        """Check if object references target GUID."""
        # Get all referenced objects
        referenced = self.resolver.get_referenced_objects(obj, object_type)

        for ref_obj, ref_type in referenced:
            ref_guid = str(ref_obj.Guid)
            if ref_guid == target_guid:
                return True

        return False

    def _get_operations(self, project: Any, object_type: str) -> Any:
        """Get operations class for object type."""
        if not hasattr(project, object_type):
            raise AttributeError(f"Project does not have operations for {object_type}")
        return getattr(project, object_type)

    def _exists_in_target(self, guid: str) -> bool:
        """Check if object exists in target project."""
        try:
            obj = self.target_project.Object(guid)
            return obj is not None
        except Exception:
            return False
