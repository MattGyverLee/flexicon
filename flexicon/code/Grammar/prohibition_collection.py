#
#   prohibition_collection.py
#
#   Class: ProhibitionCollection
#          Smart collection for ad hoc prohibition objects with type-aware
#          filtering and unified access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Smart collection class for ad hoc morphosyntactic prohibitions.

This module provides ProhibitionCollection, a smart collection that manages
ad hoc prohibitions while showing type diversity and supporting unified
operations across the three concrete types:
- MoAdhocProhibGr (Grammatical feature prohibitions)
- MoAdhocProhibMorph (Morpheme co-occurrence prohibitions)
- MoAdhocProhibAllomorph (Allomorph co-occurrence prohibitions)

Problem:
    GetAllAdhocCoProhibitions() returns objects with multiple concrete
    implementations. Users need to:
    - See which types are in the collection
    - Filter by type if they want to
    - Work with all types together without manual casting
    - Filter by common properties that work across all types

Solution:
    ProhibitionCollection provides:
    - __str__() showing type breakdown
    - by_type() filtering to specific concrete types
    - filter() for filtering by prohibition type
    - grammatical_prohibitions(), morpheme_prohibitions(),
      allomorph_prohibitions() convenience filters
    - where() for custom filtering
    - Chainable filtering: prohibitions.morpheme_prohibitions()

Example::

    from flexlibs2.code.Grammar.prohibition_collection import ProhibitionCollection

    # GetAllAdhocCoProhibitions() now returns ProhibitionCollection
    prohibitions = morphRuleOps.GetAllAdhocCoProhibitions()
    print(prohibitions)  # Shows type breakdown
    # ProhibitionCollection (12 total)
    #   MoAdhocProhibGr: 5 (42%)
    #   MoAdhocProhibMorph: 4 (33%)
    #   MoAdhocProhibAllomorph: 3 (25%)

    # Filter by type
    morph_only = prohibitions.morpheme_prohibitions()
    print(len(morph_only))  # 4

    # Filter by custom predicate
    named_prohibitions = prohibitions.where(lambda p: p.guid is not None)

    # Chain filters
    morph_with_guid = prohibitions.morpheme_prohibitions().where(
        lambda p: p.guid is not None
    )

    # Iterate
    for prohib in prohibitions:
        print(prohib.prohibition_type)
"""

from ..Shared.smart_collection import SmartCollection
from .adhoc_prohibition import AdhocProhibition


class ProhibitionCollection(SmartCollection):
    """
    Smart collection for ad hoc prohibitions with type-aware filtering.

    Manages collections of AdhocProhibition wrapper objects with type-aware
    display and filtering capabilities. Supports filtering by prohibition
    type and custom predicates.

    Attributes:
        _items: List of AdhocProhibition wrapper objects

    Example::

        prohibitions = morphRuleOps.GetAllAdhocCoProhibitions()
        print(prohibitions)  # Shows type breakdown
        morph = prohibitions.morpheme_prohibitions()  # Type filter
        custom = prohibitions.where(lambda p: p.is_morpheme_prohibition)
    """

    def __init__(self, items=None):
        """
        Initialize a ProhibitionCollection.

        Args:
            items: Iterable of AdhocProhibition objects, or None for empty.

        Example::

            collection = ProhibitionCollection()
            collection = ProhibitionCollection([prohib1, prohib2, prohib3])
        """
        super().__init__(items)

    def filter(self, prohibition_type=None, where=None):
        """
        Filter the collection by prohibition type.

        Supports filtering by prohibition type (grammatical, morpheme,
        allomorph). For complex filtering, use where().

        Args:
            prohibition_type (str, optional): Filter by type. Accepts:
                - "Grammatical" or "grammatical"
                - "Morpheme" or "morpheme"
                - "Allomorph" or "allomorph"
                - "Gr" (abbreviation for Grammatical)
                - "Morph" (abbreviation for Morpheme)
                - "Allo" (abbreviation for Allomorph)
            where (callable, optional): Custom predicate function. If provided,
                prohibition_type is ignored.

        Returns:
            ProhibitionCollection: New collection with filtered items.

        Example::

            # Filter by type name
            morph_prohibitions = prohibitions.filter(prohibition_type="Morpheme")

            # Filter by abbreviation
            gr_prohibitions = prohibitions.filter(prohibition_type="Gr")

            # Custom filtering
            has_guid = prohibitions.where(lambda p: p.guid is not None)

            # Chain filters
            morph_with_guid = prohibitions.filter(
                prohibition_type="Morpheme"
            ).where(lambda p: p.guid is not None)

        Notes:
            - prohibition_type is case-insensitive
            - Abbreviations: "Gr", "Morph", "Allo"
            - where() takes precedence over prohibition_type
            - Returns new collection (doesn't modify original)
            - Use where() for complex custom filtering
        """
        # If custom predicate provided, use it
        if where is not None:
            filtered = [item for item in self._items if where(item)]
            return ProhibitionCollection(filtered)

        # Apply prohibition_type filter
        if prohibition_type is not None:
            # Normalize prohibition_type for comparison
            prohib_type_lower = prohibition_type.lower()

            filtered = []
            for prohib in self._items:
                prohib_type_norm = prohib.prohibition_type.lower()

                # Check against full name
                if prohib_type_norm == prohib_type_lower:
                    filtered.append(prohib)
                # Check against abbreviations
                elif prohib_type_lower == "gr" and prohib_type_norm == "grammatical":
                    filtered.append(prohib)
                elif prohib_type_lower == "morph" and prohib_type_norm == "morpheme":
                    filtered.append(prohib)
                elif prohib_type_lower == "allo" and prohib_type_norm == "allomorph":
                    filtered.append(prohib)

            return ProhibitionCollection(filtered)

        # No filter applied, return copy of all items
        return ProhibitionCollection(self._items)

    def where(self, predicate):
        """
        Filter using a custom predicate function.

        For filtering by complex criteria or properties not supported by
        filter().

        Args:
            predicate (callable): Function that takes an AdhocProhibition
                and returns True to include it in the result.

        Returns:
            ProhibitionCollection: New collection with items matching the
                predicate.

        Example::

            # Prohibitions with non-empty GUID
            has_guid = prohibitions.where(lambda p: p.guid is not None)

            # Combining conditions
            morph_with_guid = prohibitions.where(
                lambda p: p.is_morpheme_prohibition and p.guid is not None
            )

            # Type checking combined with other criteria
            non_grammatical = prohibitions.where(
                lambda p: p.class_type != "MoAdhocProhibGr"
            )

        Notes:
            - Predicate receives each AdhocProhibition object
            - Return True to include in result, False to exclude
            - For simple filters (type), use filter() instead
        """
        filtered = [prohib for prohib in self._items if predicate(prohib)]
        return ProhibitionCollection(filtered)

    def grammatical_prohibitions(self):
        """
        Get only the grammatical feature prohibitions from the collection.

        Convenience method for filtering to MoAdhocProhibGr objects only.

        Returns:
            ProhibitionCollection: New collection with only MoAdhocProhibGr
                objects.

        Example::

            grammatical = prohibitions.grammatical_prohibitions()
            print(f"Found {len(grammatical)} grammatical prohibitions")

            # Chain with other filters
            with_guid = prohibitions.grammatical_prohibitions().where(
                lambda p: p.guid is not None
            )

        Notes:
            - Equivalent to filter(prohibition_type="Grammatical")
            - Use is_grammatical_prohibition on individual items to check type
        """
        return self.filter(prohibition_type="Grammatical")

    def morpheme_prohibitions(self):
        """
        Get only the morpheme co-occurrence prohibitions from the collection.

        Convenience method for filtering to MoAdhocProhibMorph objects only.

        Returns:
            ProhibitionCollection: New collection with only MoAdhocProhibMorph
                objects.

        Example::

            morpheme = prohibitions.morpheme_prohibitions()
            print(f"Found {len(morpheme)} morpheme prohibitions")

            # Chain with other filters
            morph_subset = prohibitions.morpheme_prohibitions().where(
                lambda p: p.MorphemeRA is not None
            )

        Notes:
            - Equivalent to filter(prohibition_type="Morpheme")
            - Use is_morpheme_prohibition on individual items to check type
        """
        return self.filter(prohibition_type="Morpheme")

    def allomorph_prohibitions(self):
        """
        Get only the allomorph variant prohibitions from the collection.

        Convenience method for filtering to MoAdhocProhibAllomorph objects
        only.

        Returns:
            ProhibitionCollection: New collection with only
                MoAdhocProhibAllomorph objects.

        Example::

            allomorph = prohibitions.allomorph_prohibitions()
            print(f"Found {len(allomorph)} allomorph prohibitions")

            # Chain with other filters
            allo_subset = prohibitions.allomorph_prohibitions().where(
                lambda p: p.AllomorphRA is not None
            )

        Notes:
            - Equivalent to filter(prohibition_type="Allomorph")
            - Use is_allomorph_prohibition on individual items to check type
        """
        return self.filter(prohibition_type="Allomorph")

    def __repr__(self):
        """Technical representation."""
        return f"ProhibitionCollection({len(self._items)} items)"
