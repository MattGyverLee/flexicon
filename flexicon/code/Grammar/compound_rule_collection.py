#
#   compound_rule_collection.py
#
#   Class: CompoundRuleCollection
#          Smart collection for compound rules with type-aware filtering
#          and unified access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Smart collection class for compound rules.

This module provides CompoundRuleCollection, a smart collection that manages
compound rules while showing type diversity and supporting unified operations
across the two concrete types:
- MoEndoCompound
- MoExoCompound

Problem:
    GetAll() returns objects with multiple concrete implementations. Users
    need to:
    - See which types are in the collection
    - Filter by type if they want to
    - Work with all types together without manual casting
    - Filter by common properties that work across all types

Solution:
    CompoundRuleCollection provides:
    - __str__() showing type breakdown
    - by_type() filtering to specific concrete types
    - filter() for common criteria (name_contains, head_dependency)
    - Convenience methods (endo_compounds(), exo_compounds())
    - Chainable filtering: rules.endo_compounds().filter(name_contains='V')
    - where() for custom predicates

Example::

    from flexlibs2.code.Grammar.compound_rule_collection import CompoundRuleCollection

    # GetAll() now returns CompoundRuleCollection
    rules = morphRuleOps.GetAll()
    print(rules)  # Shows type breakdown
    # CompoundRuleCollection (8 total)
    #   MoEndoCompound: 5 (62%)
    #   MoExoCompound: 3 (38%)

    # Filter by type
    endo_only = rules.endo_compounds()
    print(len(endo_only))  # 5

    # Filter by name
    verb_rules = rules.filter(name_contains='Verb')

    # Chain filters
    verb_endo = rules.endo_compounds().filter(name_contains='Verb')

    # Iterate
    for rule in rules:
        print(rule.name)
"""

from ..Shared.smart_collection import SmartCollection
from .compound_rule import CompoundRule


class CompoundRuleCollection(SmartCollection):
    """
    Smart collection for compound rules with type-aware filtering.

    Manages collections of compound rules (CompoundRule wrapper objects)
    with type-aware display and filtering capabilities. Supports filtering by
    common properties (name, head_dependency) and by concrete type.

    Attributes:
        _items: List of CompoundRule wrapper objects

    Example::

        rules = morphRuleOps.GetAll()  # Returns CompoundRuleCollection
        print(rules)  # Shows type breakdown
        endo = rules.endo_compounds()  # Filter to MoEndoCompound
        verb = rules.filter(name_contains='Verb')  # Name filter
        both = rules.endo_compounds().filter(name_contains='Verb')  # Chain
    """

    def __init__(self, items=None):
        """
        Initialize a CompoundRuleCollection.

        Args:
            items: Iterable of CompoundRule objects, or None for empty.

        Example::

            collection = CompoundRuleCollection()
            collection = CompoundRuleCollection([rule1, rule2, rule3])
        """
        super().__init__(items)

    def filter(self, name_contains=None, head_dependency=None, where=None):
        """
        Filter the collection by common rule properties.

        Supports filtering by properties that work across all rule types
        (name, head_dependency). For complex filtering, use where().

        Args:
            name_contains (str, optional): Filter to rules whose name contains
                this string (case-sensitive).
            head_dependency (int, optional): Filter by head dependency value.
            where (callable, optional): Custom predicate function. If provided,
                other criteria are ignored.

        Returns:
            CompoundRuleCollection: New collection with filtered items.

        Example::

            # Filter by name
            verb_rules = rules.filter(name_contains='Verb')

            # Filter by head dependency
            lhs_head = rules.filter(head_dependency=0)

            # Custom filtering
            with_contexts = rules.where(lambda r: r.left_context or r.right_context)

            # Chain filters
            verb_lhs = rules.filter(name_contains='Verb').filter(head_dependency=0)

        Notes:
            - name_contains is case-sensitive
            - All criteria are AND-ed together unless only one is provided
            - where() takes precedence over other criteria
            - Returns new collection (doesn't modify original)
            - Use where() for complex custom filtering
        """
        # If custom predicate provided, use it
        if where is not None:
            filtered = [item for item in self._items if where(item)]
            return CompoundRuleCollection(filtered)

        # Apply criteria filters
        filtered = self._items

        if name_contains is not None:
            filtered = [rule for rule in filtered if name_contains in (rule.name or "")]

        if head_dependency is not None:
            filtered = [rule for rule in filtered if rule.head_dependency == head_dependency]

        return CompoundRuleCollection(filtered)

    def where(self, predicate):
        """
        Filter using a custom predicate function.

        For filtering by complex criteria or properties not supported by filter().

        Args:
            predicate (callable): Function that takes a CompoundRule and
                returns True to include it in the result.

        Returns:
            CompoundRuleCollection: New collection with items matching the predicate.

        Example::

            # Complex predicate: rules with both left and right contexts
            full_context = rules.where(
                lambda r: r.left_context is not None and r.right_context is not None
            )

            # Combining conditions
            endo_with_context = rules.where(
                lambda r: r.is_endo_compound and (r.left_context or r.right_context)
            )

            # Type checking combined with other criteria
            exo_rules = rules.where(lambda r: r.is_exo_compound)

        Notes:
            - Predicate receives each CompoundRule object
            - Return True to include in result, False to exclude
            - For simple filters (name, head_dependency), use filter() instead
        """
        filtered = [rule for rule in self._items if predicate(rule)]
        return CompoundRuleCollection(filtered)

    def endo_compounds(self):
        """
        Get only the endocentric (MoEndoCompound) rules from the collection.

        Convenience method for filtering to MoEndoCompound objects only.

        Returns:
            CompoundRuleCollection: New collection with only MoEndoCompound objects.

        Example::

            endo = rules.endo_compounds()
            print(f"Found {len(endo)} endocentric rules")

            # Chain with other filters
            verb_endo = rules.endo_compounds().filter(name_contains='Verb')

        Notes:
            - Equivalent to by_type('MoEndoCompound')
            - Endo compounds have head internal to the compound
            - Use is_endo_compound on individual rules to check type
        """
        return self.by_type("MoEndoCompound")

    def exo_compounds(self):
        """
        Get only the exocentric (MoExoCompound) rules from the collection.

        Convenience method for filtering to MoExoCompound objects only.

        Returns:
            CompoundRuleCollection: New collection with only MoExoCompound objects.

        Example::

            exo = rules.exo_compounds()
            print(f"Found {len(exo)} exocentric rules")

            # Chain with other filters
            noun_exo = rules.exo_compounds().filter(name_contains='Noun')

        Notes:
            - Equivalent to by_type('MoExoCompound')
            - Exo compounds have head external to the compound
            - Use is_exo_compound on individual rules to check type
        """
        return self.by_type("MoExoCompound")

    def __repr__(self):
        """Technical representation."""
        return f"CompoundRuleCollection({len(self._items)} rules)"
