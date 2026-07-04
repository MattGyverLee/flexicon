#
#   smart_collection.py
#
#   Class: SmartCollection
#          Base class for smart collections showing type diversity while
#          supporting unified operations across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Base class for smart collections with type-aware display and filtering.

This module provides SmartCollection, a base class for creating collection
objects that present multiple concrete types in a unified way while still
showing the type diversity to the user.

The Problem:
    When you call GetAll() on an operation class that returns objects with
    multiple concrete implementations (e.g., phonological rules), the collection
    mixes different types. Users need to:
    - See which types are represented
    - Filter by type if they want to
    - Work with all types together without manual casting

The Solution:
    SmartCollection provides:
    - __str__() that shows type breakdown by ClassName count
    - by_type() method to filter to specific concrete types
    - filter() abstract method for subclasses to define filtering logic
    - Standard Python collection methods (__iter__, __len__)

Example::

    from flexlibs2.code.Shared.smart_collection import SmartCollection

    class RuleCollection(SmartCollection):
        def filter(self, **criteria):
            '''Filter rules by name, direction, etc.'''
            filtered = [r for r in self._items if self._matches(r, criteria)]
            return RuleCollection(filtered)

    # Usage
    rules = phonRuleOps.GetAll()  # Returns RuleCollection with 12 rules
    print(rules)  # Shows type breakdown
    # "Phonological Rules (12 total)"
    # "  PhRegularRule: 7 (58%)"
    # "  PhMetathesisRule: 3 (25%)"
    # "  PhReduplicationRule: 2 (17%)"

    # Filter to specific type
    regular_rules = rules.by_type('PhRegularRule')
    print(len(regular_rules))  # 7

    # Use custom filter
    voicing_rules = rules.filter(name_contains='voicing')

Usage Notes:
    - Subclasses must override filter() to provide filtering logic
    - Collections are iterable and support len()
    - Type breakdown is shown on str() for transparency
    - by_type() is implemented in base class
"""

from collections.abc import Iterable


class SmartCollection(Iterable):
    """
    Base class for smart collections with type awareness and unified filtering.

    Provides standard collection operations (__iter__, __len__, __str__)
    plus type-aware features (by_type filtering, type breakdown display).

    Subclasses override filter() to define domain-specific filtering logic.

    Attributes:
        _items: The list of wrapped LCM objects in the collection
    """

    def __init__(self, items=None):
        """
        Initialize a smart collection with items.

        Args:
            items: Iterable of items, or None for empty collection.

        Example::

            collection = SmartCollection()
            collection = SmartCollection([item1, item2, item3])
        """
        if items is None:
            self._items = []
        else:
            self._items = list(items)

    def __iter__(self):
        """
        Iterate over items in the collection.

        Supports natural iteration and unpacking:

        Example::

            for rule in rules:
                print(rule.Name)

            first, second, *rest = rules
        """
        return iter(self._items)

    def __len__(self):
        """
        Get the number of items in the collection.

        Returns:
            int: Number of items.

        Example::

            rules = phonRuleOps.GetAll()
            print(f"Collection has {len(rules)} rules")
        """
        return len(self._items)

    def __getitem__(self, index):
        """
        Get an item by index (supports indexing and slicing).

        Args:
            index: Integer index or slice object.

        Returns:
            Single item or new SmartCollection with sliced items.

        Example::

            first_rule = rules[0]
            first_three = rules[0:3]  # Returns new SmartCollection
        """
        result = self._items[index]
        # If it's a slice, wrap in new collection
        if isinstance(index, slice):
            return type(self)(result)
        return result

    def __str__(self):
        """
        Display the collection with type breakdown.

        Shows the total count and a breakdown of items by ClassName,
        making type diversity visible to the user.

        Returns:
            str: Human-readable summary like:
                "Phonological Rules (12 total)"
                "  PhRegularRule: 7 (58%)"
                "  PhMetathesisRule: 3 (25%)"
                "  PhReduplicationRule: 2 (17%)"

        Example::

            rules = phonRuleOps.GetAll()
            print(rules)  # Shows type breakdown
        """
        if not self._items:
            return f"{type(self).__name__} (empty)"

        # Count items by ClassName
        type_counts = {}
        for item in self._items:
            class_type = getattr(item, "class_type", getattr(item, "ClassName", "Unknown"))
            type_counts[class_type] = type_counts.get(class_type, 0) + 1

        # Build summary
        total = len(self._items)
        lines = [f"{type(self).__name__} ({total} total)"]

        # Add breakdown by type (sorted by count descending)
        for class_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = int(count * 100 / total)
            lines.append(f"  {class_type}: {count} ({percentage}%)")

        return "\n".join(lines)

    def __repr__(self):
        """
        Technical representation of the collection.

        Returns:
            str: Representation like "SmartCollection(12 items)"
        """
        return f"{type(self).__name__}({len(self._items)} items)"

    def by_type(self, class_name):
        """
        Filter the collection to items of a specific concrete type.

        Returns a new collection containing only items whose ClassName
        matches the specified class_name. Useful for operating on a
        specific concrete type (e.g., just PhRegularRule, not all rules).

        Args:
            class_name: The ClassName to filter by (e.g., 'PhRegularRule').

        Returns:
            SmartCollection: New collection with filtered items.

        Example::

            all_rules = phonRuleOps.GetAll()
            regular_rules = all_rules.by_type('PhRegularRule')
            print(f"Found {len(regular_rules)} regular rules")

            # Chain with custom filtering
            voicing_regular = regular_rules.filter(name_contains='voicing')

        Notes:
            - Returns a new collection (doesn't modify original)
            - Returns empty collection if no items match
            - Use ClassName strings like 'PhRegularRule', 'MoStemMsa', etc.
        """
        filtered = [
            item for item in self._items if getattr(item, "class_type", getattr(item, "ClassName", None)) == class_name
        ]
        return type(self)(filtered)

    def filter(self, **criteria):
        """
        Filter the collection using domain-specific criteria.

        This is an abstract method that subclasses override to provide
        filtering logic specific to their domain. For example:
        - RuleCollection.filter(name_contains='voicing', direction='LTR')
        - EntryCollection.filter(gloss_contains='to run', pos='verb')

        Subclasses should return a new collection of the same type with
        items matching all criteria.

        Args:
            **criteria: Domain-specific filter criteria.

        Returns:
            SmartCollection: New collection with filtered items.

        Raises:
            NotImplementedError: Base class doesn't implement filtering.
                Subclasses must override this method.

        Example::

            # Subclass implementation
            class RuleCollection(SmartCollection):
                def filter(self, name_contains=None, direction=None):
                    filtered = self._items
                    if name_contains:
                        filtered = [
                            r for r in filtered
                            if name_contains in r.Name
                        ]
                    if direction:
                        filtered = [
                            r for r in filtered
                            if r.Direction == direction
                        ]
                    return RuleCollection(filtered)

            # Usage
            voicing_rules = rules.filter(name_contains='voicing')
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement filter(). "
            "Subclasses must override this method to provide filtering logic."
        )

    def append(self, item):
        """
        Add an item to the collection.

        Args:
            item: Item to add.

        Example::

            rules = SmartCollection()
            rules.append(new_rule)
        """
        self._items.append(item)

    def extend(self, items):
        """
        Add multiple items to the collection.

        Args:
            items: Iterable of items to add.

        Example::

            rules.extend([rule1, rule2, rule3])
        """
        self._items.extend(items)

    def clear(self):
        """
        Remove all items from the collection.

        Example::

            rules.clear()
            assert len(rules) == 0
        """
        self._items.clear()
