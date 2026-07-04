#
#   rule_collection.py
#
#   Class: RuleCollection
#          Smart collection for phonological rules with type-aware filtering
#          and unified access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Smart collection class for phonological rules.

This module provides RuleCollection, a smart collection that manages
phonological rules while showing type diversity and supporting unified
operations across the three concrete types:
- PhRegularRule
- PhMetathesisRule
- PhReduplicationRule

Problem:
    GetAll() returns objects with multiple concrete implementations. Users
    need to:
    - See which types are in the collection
    - Filter by type if they want to
    - Work with all types together without manual casting
    - Filter by common properties that work across all types

Solution:
    RuleCollection provides:
    - __str__() showing type breakdown
    - by_type() filtering to specific concrete types
    - filter() for common criteria (name_contains, direction, stratum)
    - Convenience methods (regular_rules(), metathesis_rules(), redup_rules())
    - Chainable filtering: rules.regular_rules().filter(name_contains='voicing')

Example::

    from flexlibs2.code.Grammar.rule_collection import RuleCollection

    # GetAll() now returns RuleCollection
    rules = phonRuleOps.GetAll()
    print(rules)  # Shows type breakdown
    # RuleCollection (12 total)
    #   PhRegularRule: 7 (58%)
    #   PhMetathesisRule: 3 (25%)
    #   PhReduplicationRule: 2 (17%)

    # Filter by type
    regular_only = rules.regular_rules()
    print(len(regular_only))  # 7

    # Filter by name
    voicing_rules = rules.filter(name_contains='voicing')

    # Chain filters
    voicing_regular = rules.regular_rules().filter(name_contains='voicing')

    # Iterate
    for rule in rules:
        print(rule.name)
"""

from ..Shared.smart_collection import SmartCollection
from .phonological_rule import PhonologicalRule


class RuleCollection(SmartCollection):
    """
    Smart collection for phonological rules with type-aware filtering.

    Manages collections of phonological rules (PhonologicalRule wrapper objects)
    with type-aware display and filtering capabilities. Supports filtering by
    common properties (name, direction, stratum) and by concrete type.

    Attributes:
        _items: List of PhonologicalRule wrapper objects

    Example::

        rules = phonRuleOps.GetAll()  # Returns RuleCollection
        print(rules)  # Shows type breakdown
        regular = rules.regular_rules()  # Filter to PhRegularRule
        voicing = rules.filter(name_contains='voicing')  # Name filter
        both = rules.regular_rules().filter(name_contains='voicing')  # Chain
    """

    def __init__(self, items=None):
        """
        Initialize a RuleCollection.

        Args:
            items: Iterable of PhonologicalRule objects, or None for empty.

        Example::

            collection = RuleCollection()
            collection = RuleCollection([rule1, rule2, rule3])
        """
        super().__init__(items)

    def filter(self, name_contains=None, direction=None, stratum=None, where=None):
        """
        Filter the collection by common rule properties.

        Supports filtering by properties that work across all rule types
        (name, direction, stratum). For complex filtering, use where().

        Args:
            name_contains (str, optional): Filter to rules whose name contains
                this string (case-sensitive).
            direction (int, optional): Filter by direction (0=L-R, 1=R-L, 2=simultaneous).
            stratum: Filter by stratum object or GUID. Can be an IMoStratum
                object or the stratum GUID as string.
            where (callable, optional): Custom predicate function. If provided,
                other criteria are ignored.

        Returns:
            RuleCollection: New collection with filtered items.

        Example::

            # Filter by name
            voicing_rules = rules.filter(name_contains='voicing')

            # Filter by direction
            ltr_rules = rules.filter(direction=0)

            # Filter by stratum
            stratum = project.lp.MorphologicalDataOA.StrataOS[0]
            stratum_rules = rules.filter(stratum=stratum)

            # Custom filtering
            high_rules = rules.where(lambda r: r.Direction == 0)

            # Chain filters
            voicing_ltr = rules.filter(name_contains='voicing').filter(direction=0)

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
            return RuleCollection(filtered)

        # Apply criteria filters
        filtered = self._items

        if name_contains is not None:
            filtered = [rule for rule in filtered if name_contains in (rule.name or "")]

        if direction is not None:
            filtered = [rule for rule in filtered if rule.direction == direction]

        if stratum is not None:
            # Handle both object and GUID comparisons
            stratum_guid = None
            if stratum is not None:
                if hasattr(stratum, "Guid"):
                    stratum_guid = str(stratum.Guid)
                else:
                    stratum_guid = str(stratum)

            filtered = [
                rule
                for rule in filtered
                if rule.stratum is not None and (str(rule.stratum.Guid) == stratum_guid if stratum_guid else False)
            ]

        return RuleCollection(filtered)

    def where(self, predicate):
        """
        Filter using a custom predicate function.

        For filtering by complex criteria or properties not supported by filter().

        Args:
            predicate (callable): Function that takes a PhonologicalRule and
                returns True to include it in the result.

        Returns:
            RuleCollection: New collection with items matching the predicate.

        Example::

            # Complex predicate: rules with more than 2 input contexts
            complex_rules = rules.where(lambda r: len(r.input_contexts) > 2)

            # Combining conditions
            regular_with_contexts = rules.where(
                lambda r: r.has_output_specs and len(r.input_contexts) > 1
            )

            # Type checking combined with other criteria
            non_regular = rules.where(lambda r: r.class_type != 'PhRegularRule')

        Notes:
            - Predicate receives each PhonologicalRule object
            - Return True to include in result, False to exclude
            - For simple filters (name, direction), use filter() instead
        """
        filtered = [rule for rule in self._items if predicate(rule)]
        return RuleCollection(filtered)

    def regular_rules(self):
        """
        Get only the regular (PhRegularRule) rules from the collection.

        Convenience method for filtering to PhRegularRule objects only.

        Returns:
            RuleCollection: New collection with only PhRegularRule objects.

        Example::

            regular = rules.regular_rules()
            print(f"Found {len(regular)} regular rules")

            # Chain with other filters
            voicing_regular = rules.regular_rules().filter(name_contains='voicing')

        Notes:
            - Equivalent to by_type('PhRegularRule')
            - Regular rules have RightHandSidesOS (output specifications)
            - Use has_output_specs on individual rules to check type
        """
        return self.by_type("PhRegularRule")

    def metathesis_rules(self):
        """
        Get only the metathesis (PhMetathesisRule) rules from the collection.

        Convenience method for filtering to PhMetathesisRule objects only.

        Returns:
            RuleCollection: New collection with only PhMetathesisRule objects.

        Example::

            metathesis = rules.metathesis_rules()
            print(f"Found {len(metathesis)} metathesis rules")

            # Chain with other filters
            initial_metathesis = rules.metathesis_rules().filter(name_contains='initial')

        Notes:
            - Equivalent to by_type('PhMetathesisRule')
            - Metathesis rules swap segments (left <-> right)
            - Use has_metathesis_parts on individual rules to check type
        """
        return self.by_type("PhMetathesisRule")

    def redup_rules(self):
        """
        Get only the reduplication (PhReduplicationRule) rules from the collection.

        Convenience method for filtering to PhReduplicationRule objects only.

        Returns:
            RuleCollection: New collection with only PhReduplicationRule objects.

        Example::

            redup = rules.redup_rules()
            print(f"Found {len(redup)} reduplication rules")

            # Chain with other filters
            prefix_redup = rules.redup_rules().filter(name_contains='prefix')

        Notes:
            - Equivalent to by_type('PhReduplicationRule')
            - Reduplication rules repeat segments
            - Use has_redup_parts on individual rules to check type
        """
        return self.by_type("PhReduplicationRule")

    def __repr__(self):
        """Technical representation."""
        return f"RuleCollection({len(self._items)} rules)"
