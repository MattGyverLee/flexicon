#
#   allomorph_collection.py
#
#   Class: AllomorphCollection
#          Smart collection for allomorphs with type-aware filtering
#          and unified access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Smart collection class for allomorphs.

This module provides AllomorphCollection, a smart collection that manages
allomorphs while showing type diversity and supporting unified operations
across the two concrete types:
- MoStemAllomorph
- MoAffixAllomorph

Problem:
    GetAll() returns objects with multiple concrete implementations. Users
    need to:
    - See which types are in the collection
    - Filter by type if they want to
    - Work with all types together without manual casting
    - Filter by common properties that work across all types

Solution:
    AllomorphCollection provides:
    - __str__() showing type breakdown
    - by_type() filtering to specific concrete types
    - filter() for common criteria (form_contains, environment, type)
    - Convenience methods (stem_allomorphs(), affix_allomorphs())
    - Chainable filtering: allomorphs.stem_allomorphs().filter(form_contains='ing')

Example::

    from flexlibs2.code.Lexicon.allomorph_collection import AllomorphCollection

    # GetAll() now returns AllomorphCollection
    allomorphs = allomorphOps.GetAll(entry)
    print(allomorphs)  # Shows type breakdown
    # AllomorphCollection (8 total)
    #   MoStemAllomorph: 5 (62%)
    #   MoAffixAllomorph: 3 (38%)

    # Filter by type
    stems = allomorphs.stem_allomorphs()
    print(len(stems))  # 5

    # Filter by form
    ing_allomorphs = allomorphs.filter(form_contains='ing')

    # Chain filters
    ing_stems = allomorphs.stem_allomorphs().filter(form_contains='ing')

    # Iterate
    for allomorph in allomorphs:
        print(allomorph.form)
"""

from ..Shared.smart_collection import SmartCollection
from .allomorph import Allomorph


class AllomorphCollection(SmartCollection):
    """
    Smart collection for allomorphs with type-aware filtering.

    Manages collections of allomorph (Allomorph wrapper objects) with
    type-aware display and filtering capabilities. Supports filtering by
    common properties (form, environment, type) and by concrete type.

    Attributes:
        _items: List of Allomorph wrapper objects

    Example::

        allomorphs = allomorphOps.GetAll(entry)  # Returns AllomorphCollection
        print(allomorphs)  # Shows type breakdown
        stems = allomorphs.stem_allomorphs()  # Filter to MoStemAllomorph
        ing = allomorphs.filter(form_contains='ing')  # Form filter
        both = allomorphs.stem_allomorphs().filter(form_contains='ing')  # Chain
    """

    def __init__(self, items=None):
        """
        Initialize an AllomorphCollection.

        Args:
            items: Iterable of Allomorph objects, or None for empty.

        Example::

            collection = AllomorphCollection()
            collection = AllomorphCollection([allomorph1, allomorph2, allomorph3])
        """
        super().__init__(items)

    def filter(self, form_contains=None, environment=None, where=None):
        """
        Filter the collection by common allomorph properties.

        Supports filtering by properties that work across all allomorph types
        (form, environment). For complex filtering, use where().

        Args:
            form_contains (str, optional): Filter to allomorphs whose form contains
                this string (case-sensitive).
            environment: Filter by environment object or GUID. Can be an IPhEnvironment
                object or the environment GUID as string.
            where (callable, optional): Custom predicate function. If provided,
                other criteria are ignored.

        Returns:
            AllomorphCollection: New collection with filtered items.

        Example::

            # Filter by form
            ing_allomorphs = allomorphs.filter(form_contains='ing')

            # Filter by environment
            env = project.lp.PhonologicalDataOA.EnvironmentsOS[0]
            env_allomorphs = allomorphs.filter(environment=env)

            # Custom filtering
            long_forms = allomorphs.where(lambda a: len(a.form) > 3)

            # Chain filters
            ing_stems = allomorphs.filter(form_contains='ing').stem_allomorphs()

        Notes:
            - form_contains is case-sensitive
            - All criteria are AND-ed together unless only one is provided
            - where() takes precedence over other criteria
            - Returns new collection (doesn't modify original)
            - Use where() for complex custom filtering
        """
        # If custom predicate provided, use it
        if where is not None:
            filtered = [item for item in self._items if where(item)]
            return AllomorphCollection(filtered)

        # Apply criteria filters
        filtered = self._items

        if form_contains is not None:
            filtered = [allomorph for allomorph in filtered if form_contains in (allomorph.form or "")]

        if environment is not None:
            # Handle both object and GUID comparisons
            environment_guid = None
            if environment is not None:
                if hasattr(environment, "Guid"):
                    environment_guid = str(environment.Guid)
                else:
                    environment_guid = str(environment)

            filtered = [
                allomorph
                for allomorph in filtered
                if any(str(env.Guid) == environment_guid for env in allomorph.environment)
            ]

        return AllomorphCollection(filtered)

    def where(self, predicate):
        """
        Filter using a custom predicate function.

        For filtering by complex criteria or properties not supported by filter().

        Args:
            predicate (callable): Function that takes an Allomorph and
                returns True to include it in the result.

        Returns:
            AllomorphCollection: New collection with items matching the predicate.

        Example::

            # Complex predicate: allomorphs with form length > 3
            long_forms = allomorphs.where(lambda a: len(a.form) > 3)

            # Combining conditions
            stem_with_env = allomorphs.where(
                lambda a: a.is_stem_allomorph and len(a.environment) > 0
            )

            # Type checking combined with other criteria
            affix_only = allomorphs.where(lambda a: a.is_affix_allomorph)

        Notes:
            - Predicate receives each Allomorph object
            - Return True to include in result, False to exclude
            - For simple filters (form, environment), use filter() instead
        """
        filtered = [allomorph for allomorph in self._items if predicate(allomorph)]
        return AllomorphCollection(filtered)

    def stem_allomorphs(self):
        """
        Get only the stem allomorphs from the collection.

        Convenience method for filtering to MoStemAllomorph objects only.

        Returns:
            AllomorphCollection: New collection with only MoStemAllomorph objects.

        Example::

            stems = allomorphs.stem_allomorphs()
            print(f"Found {len(stems)} stem allomorphs")

            # Chain with other filters
            ing_stems = allomorphs.stem_allomorphs().filter(form_contains='ing')

        Notes:
            - Equivalent to by_type('MoStemAllomorph')
            - Stem allomorphs are variants of stems/roots
            - Use is_stem_allomorph on individual allomorphs to check type
        """
        return self.by_type("MoStemAllomorph")

    def affix_allomorphs(self):
        """
        Get only the affix allomorphs from the collection.

        Convenience method for filtering to MoAffixAllomorph objects only.

        Returns:
            AllomorphCollection: New collection with only MoAffixAllomorph objects.

        Example::

            affixes = allomorphs.affix_allomorphs()
            print(f"Found {len(affixes)} affix allomorphs")

            # Chain with other filters
            ing_affixes = allomorphs.affix_allomorphs().filter(form_contains='ing')

        Notes:
            - Equivalent to by_type('MoAffixAllomorph')
            - Affix allomorphs are variants of prefixes, suffixes, infixes, etc.
            - Use is_affix_allomorph on individual allomorphs to check type
        """
        return self.by_type("MoAffixAllomorph")

    def __repr__(self):
        """Technical representation."""
        return f"AllomorphCollection({len(self._items)} allomorphs)"
