"""
Dependency Resolver - Phase 3.2

Discovers and resolves object dependencies by analyzing FLEx object relationships.

Author: FlexTools Development Team
Date: 2025-11-27
"""

import logging
from typing import Any, List, Tuple, Optional, Set, Dict
from dataclasses import dataclass, field

from .dependency_graph import DependencyGraph, DependencyType

logger = logging.getLogger(__name__)


@dataclass
class DependencyConfig:
    """Configuration for dependency resolution."""

    # What to include
    include_owned: bool = True  # Import owned objects (children)
    resolve_references: bool = True  # Import referenced objects
    include_referring: bool = False  # Import objects that refer to this

    # Depth limits
    max_owned_depth: int = 10  # How deep to traverse ownership hierarchy
    max_reference_depth: int = 2  # How deep to follow references

    # Filtering
    owned_types: Optional[List[str]] = None  # Which owned types to include (None = all)
    reference_types: Optional[List[str]] = None  # Which reference types to follow

    # Behavior
    skip_existing: bool = True  # Skip objects that exist in target
    create_stub_parents: bool = False  # Create minimal parent objects if missing

    # Safety
    validate_all: bool = True  # Validate all objects before import
    allow_cycles: bool = False  # Allow circular dependencies


class DependencyResolver:
    """
    Analyzes FLEx objects and discovers all dependencies.

    Builds dependency graph by examining object ownership, references,
    and cross-references.
    """

    def __init__(self, source_project: Any, target_project: Any):
        """
        Initialize dependency resolver.

        Args:
            source_project: Source FlexProject
            target_project: Target FlexProject
        """
        self.source_project = source_project
        self.target_project = target_project

        # Cache for existence checks
        self._existence_cache: Dict[str, bool] = {}

        # Known FLEx ownership relationships
        self.ownership_map = {
            "LexEntry": [
                ("LexemeFormOA", "MoForm"),
                ("AlternateFormsOS", "MoForm"),
                ("PronunciationsOS", "LexPronunciation"),
                ("SensesOS", "LexSense"),
                ("EtymologyOS", "LexEtymology"),
                ("VariantEntryTypesRS", "LexEntryRef"),
            ],
            "LexSense": [
                ("ExamplesOS", "LexExampleSentence"),
                ("SensesOS", "LexSense"),  # Subsenses
            ],
            "MoForm": [
                ("PhonEnvironmentsRC", "PhEnvironment"),
            ],
            "Allomorph": [
                ("PhonEnvironmentsRC", "PhEnvironment"),
            ],
        }

        # Known FLEx reference relationships
        self.reference_map = {
            "LexSense": [
                ("MorphoSyntaxAnalysisRA", "PartOfSpeech"),
                ("SemanticDomainsRC", "CmSemanticDomain"),
            ],
            "MoForm": [
                ("MorphTypeRA", "MoMorphType"),
            ],
            "Allomorph": [
                ("MorphTypeRA", "MoMorphType"),
            ],
            "LexEntry": [
                ("VariantFormEntryBackRefs", "LexEntry"),  # Variant relationships
            ],
        }

    def resolve_dependencies(
        self, obj: Any, object_type: str, config: Optional[DependencyConfig] = None
    ) -> DependencyGraph:
        """
        Build dependency graph for object and its dependencies.

        Args:
            obj: FLEx object to analyze
            object_type: Type of object
            config: Dependency resolution configuration

        Returns:
            DependencyGraph with all dependencies
        """
        if config is None:
            config = DependencyConfig()

        graph = DependencyGraph()
        visited: Set[str] = set()  # Prevent infinite recursion

        # Start recursive resolution
        self._resolve_recursive(
            obj=obj,
            object_type=object_type,
            graph=graph,
            config=config,
            visited=visited,
            current_owned_depth=0,
            current_ref_depth=0,
        )

        return graph

    def _resolve_recursive(
        self,
        obj: Any,
        object_type: str,
        graph: DependencyGraph,
        config: DependencyConfig,
        visited: Set[str],
        current_owned_depth: int,
        current_ref_depth: int,
    ):
        """
        Recursively resolve dependencies.

        Args:
            obj: Current object
            object_type: Type of object
            graph: Dependency graph being built
            config: Configuration
            visited: Set of visited GUIDs
            current_owned_depth: Current depth in ownership hierarchy
            current_ref_depth: Current depth in reference chain
        """
        # Get object GUID
        if not hasattr(obj, "Guid"):
            return

        guid = str(obj.Guid)

        # Check if already visited
        if guid in visited:
            return

        visited.add(guid)

        # Add object to graph
        graph.add_object(guid, object_type, obj)

        # Check if exists in target
        if config.skip_existing and self._exists_in_target(guid):
            logger.debug(f"Object {guid} already exists in target, skipping dependencies")
            return

        # Resolve owned objects (children)
        if config.include_owned and current_owned_depth < config.max_owned_depth:
            owned_objects = self.get_owned_objects(obj, object_type)

            for owned_obj, owned_type in owned_objects:
                # Filter by type if specified
                if config.owned_types and owned_type not in config.owned_types:
                    continue

                owned_guid = str(owned_obj.Guid)

                # Add ownership dependency (child depends on parent)
                graph.add_dependency(owned_guid, guid, DependencyType.OWNERSHIP)

                # Recursively resolve owned object
                self._resolve_recursive(
                    obj=owned_obj,
                    object_type=owned_type,
                    graph=graph,
                    config=config,
                    visited=visited,
                    current_owned_depth=current_owned_depth + 1,
                    current_ref_depth=current_ref_depth,
                )

        # Resolve referenced objects
        if config.resolve_references and current_ref_depth < config.max_reference_depth:
            referenced_objects = self.get_referenced_objects(obj, object_type)

            for ref_obj, ref_type in referenced_objects:
                # Filter by type if specified
                if config.reference_types and ref_type not in config.reference_types:
                    continue

                ref_guid = str(ref_obj.Guid)

                # Add reference dependency (this object depends on referenced object)
                graph.add_dependency(guid, ref_guid, DependencyType.REFERENCE)

                # Check if referenced object exists in target
                if not self._exists_in_target(ref_guid):
                    # Referenced object doesn't exist - need to import it from source
                    # Try to get it from source
                    source_ref_obj = self._get_from_source(ref_guid)
                    if source_ref_obj:
                        # Recursively resolve (but don't go too deep on references)
                        self._resolve_recursive(
                            obj=source_ref_obj,
                            object_type=ref_type,
                            graph=graph,
                            config=config,
                            visited=visited,
                            current_owned_depth=0,  # Reset owned depth for references
                            current_ref_depth=current_ref_depth + 1,
                        )
                    else:
                        # Referenced object not in source either - just add to graph
                        graph.add_object(ref_guid, ref_type, None)
                else:
                    # Exists in target - just note the dependency
                    graph.add_object(ref_guid, ref_type, None)

    def get_owned_objects(self, obj: Any, object_type: str) -> List[Tuple[Any, str]]:
        """
        Get all objects owned by this object.

        Args:
            obj: FLEx object
            object_type: Type of object

        Returns:
            List of (owned_object, object_type) tuples
        """
        owned = []

        # Get ownership relationships for this type
        relationships = self.ownership_map.get(object_type, [])

        for property_name, owned_type in relationships:
            if not hasattr(obj, property_name):
                continue

            prop_value = getattr(obj, property_name)

            if prop_value is None:
                continue

            # Handle single owned object (OA suffix)
            if property_name.endswith("OA"):
                owned.append((prop_value, owned_type))

            # Handle collection of owned objects (OS/OC suffix)
            elif property_name.endswith("OS") or property_name.endswith("OC"):
                try:
                    for owned_obj in prop_value:
                        owned.append((owned_obj, owned_type))
                except TypeError:
                    # Not iterable
                    logger.warning(f"Property {property_name} on {object_type} is not iterable")

        return owned

    def get_referenced_objects(self, obj: Any, object_type: str) -> List[Tuple[Any, str]]:
        """
        Get all objects referenced by this object.

        Args:
            obj: FLEx object
            object_type: Type of object

        Returns:
            List of (referenced_object, object_type) tuples
        """
        referenced = []

        # Get reference relationships for this type
        relationships = self.reference_map.get(object_type, [])

        for property_name, ref_type in relationships:
            if not hasattr(obj, property_name):
                continue

            prop_value = getattr(obj, property_name)

            if prop_value is None:
                continue

            # Handle single reference (RA suffix)
            if property_name.endswith("RA"):
                referenced.append((prop_value, ref_type))

            # Handle collection of references (RC suffix)
            elif property_name.endswith("RC") or property_name.endswith("RS"):
                try:
                    for ref_obj in prop_value:
                        referenced.append((ref_obj, ref_type))
                except TypeError:
                    # Not iterable
                    logger.warning(f"Property {property_name} on {object_type} is not iterable")

        return referenced

    def _exists_in_target(self, guid: str) -> bool:
        """
        Check if object exists in target project.

        Args:
            guid: Object GUID

        Returns:
            True if exists, False otherwise
        """
        # Check cache first
        if guid in self._existence_cache:
            return self._existence_cache[guid]

        # Check target project
        try:
            obj = self.target_project.Object(guid)
            exists = obj is not None
        except Exception:
            exists = False

        # Cache result
        self._existence_cache[guid] = exists
        return exists

    def _get_from_source(self, guid: str) -> Optional[Any]:
        """
        Get object from source project by GUID.

        Args:
            guid: Object GUID

        Returns:
            Object if found, None otherwise
        """
        try:
            return self.source_project.Object(guid)
        except Exception:
            return None

    def clear_cache(self):
        """Clear existence cache."""
        self._existence_cache.clear()
