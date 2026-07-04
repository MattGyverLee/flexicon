#
#   context_collection.py
#
#   Class: ContextCollection
#          Smart collection for phonological contexts with type-aware filtering
#          and unified access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Smart collection class for phonological contexts.

This module provides ContextCollection, a smart collection that manages
phonological contexts while showing type diversity and supporting unified
operations across the multiple concrete types:
- PhSimpleContextSeg
- PhSimpleContextNC
- PhComplexContextSeg
- PhComplexContextNC
- PhBoundaryContext

Problem:
    GetAll() or input_contexts returns objects with multiple concrete implementations.
    Users need to:
    - See which types are in the collection
    - Filter by type if they want to
    - Work with all types together without manual casting
    - Filter by common properties that work across all types

Solution:
    ContextCollection provides:
    - __str__() showing type breakdown
    - by_type() filtering to specific concrete types
    - filter() for common criteria (context_name, type)
    - Convenience methods (simple_contexts(), complex_contexts(), boundary_contexts())
    - Chainable filtering: contexts.simple_contexts().filter(name_contains='word')

Example::

    from flexlibs2.code.System.context_collection import ContextCollection

    # Rule's input contexts now wrapped in ContextCollection
    contexts = rule.input_contexts  # Returns ContextCollection
    print(contexts)  # Shows type breakdown
    # ContextCollection (8 total)
    #   PhSimpleContextSeg: 4 (50%)
    #   PhBoundaryContext: 3 (37%)
    #   PhSimpleContextNC: 1 (13%)

    # Filter by type
    simple_only = contexts.simple_contexts()
    print(len(simple_only))  # 5

    # Filter by name
    word_contexts = contexts.filter(name_contains='word')

    # Chain filters
    simple_word = contexts.simple_contexts().filter(name_contains='word')

    # Iterate
    for context in contexts:
        print(context.context_name)
"""

from ..Shared.smart_collection import SmartCollection
from .phonological_context import PhonologicalContext


class ContextCollection(SmartCollection):
    """
    Smart collection for phonological contexts with type-aware filtering.

    Manages collections of phonological contexts (PhonologicalContext wrapper objects)
    with type-aware display and filtering capabilities. Supports filtering by
    common properties (name, type) and by concrete type.

    Attributes:
        _items: List of PhonologicalContext wrapper objects

    Example::

        contexts = rule.input_contexts  # Returns ContextCollection
        print(contexts)  # Shows type breakdown
        simple = contexts.simple_contexts()  # Filter to simple contexts
        word = contexts.filter(name_contains='word')  # Name filter
        both = contexts.simple_contexts().filter(name_contains='word')  # Chain
    """

    def __init__(self, items=None):
        """
        Initialize a ContextCollection.

        Args:
            items: Iterable of PhonologicalContext objects, or None for empty.

        Example::

            collection = ContextCollection()
            collection = ContextCollection([context1, context2, context3])
        """
        super().__init__(items)

    def filter(self, name_contains=None, where=None):
        """
        Filter the collection by common context properties.

        Supports filtering by properties that work across all context types
        (name). For complex filtering, use where().

        Args:
            name_contains (str, optional): Filter to contexts whose name contains
                this string (case-sensitive).
            where (callable, optional): Custom predicate function. If provided,
                other criteria are ignored.

        Returns:
            ContextCollection: New collection with filtered items.

        Example::

            # Filter by name
            word_contexts = contexts.filter(name_contains='word')

            # Custom filtering
            simple_word = contexts.where(
                lambda c: c.is_simple_context and 'word' in c.context_name
            )

            # Chain filters
            simple_word = contexts.simple_contexts().filter(name_contains='word')

        Notes:
            - name_contains is case-sensitive
            - where() takes precedence over other criteria
            - Returns new collection (doesn't modify original)
            - Use where() for complex custom filtering
        """
        # If custom predicate provided, use it
        if where is not None:
            filtered = [item for item in self._items if where(item)]
            return ContextCollection(filtered)

        # Apply criteria filters
        filtered = self._items

        if name_contains is not None:
            filtered = [ctx for ctx in filtered if name_contains in (ctx.context_name or "")]

        return ContextCollection(filtered)

    def where(self, predicate):
        """
        Filter using a custom predicate function.

        For filtering by complex criteria or properties not supported by filter().

        Args:
            predicate (callable): Function that takes a PhonologicalContext and
                returns True to include it in the result.

        Returns:
            ContextCollection: New collection with items matching the predicate.

        Example::

            # Complex predicate: simple segment contexts only
            simple_segs = contexts.where(lambda c: c.is_simple_context_seg)

            # Combining conditions
            simple_with_name = contexts.where(
                lambda c: c.is_simple_context and c.context_name
            )

        Notes:
            - Predicate receives each PhonologicalContext object
            - Return True to include in result, False to exclude
            - For simple filters (name), use filter() instead
        """
        filtered = [ctx for ctx in self._items if predicate(ctx)]
        return ContextCollection(filtered)

    def simple_contexts(self):
        """
        Get only the simple contexts (segment or natural class).

        Convenience method for filtering to simple contexts (either
        PhSimpleContextSeg or PhSimpleContextNC).

        Returns:
            ContextCollection: New collection with only simple context objects.

        Example::

            simple = contexts.simple_contexts()
            print(f"Found {len(simple)} simple contexts")

            # Chain with other filters
            simple_word = contexts.simple_contexts().filter(name_contains='word')

        Notes:
            - Includes both PhSimpleContextSeg and PhSimpleContextNC
            - Use simple_context_seg() or simple_context_nc() to distinguish
        """
        filtered = [ctx for ctx in self._items if ctx.is_simple_context]
        return ContextCollection(filtered)

    def simple_context_seg(self):
        """
        Get only the simple segment contexts.

        Convenience method for filtering to PhSimpleContextSeg objects only.

        Returns:
            ContextCollection: New collection with only simple segment contexts.

        Example::

            segs = contexts.simple_context_seg()
            for seg_ctx in segs:
                segment = seg_ctx.segment
                print(f"Segment: {segment}")

        Notes:
            - Simple segment contexts represent a single segment
            - Equivalent to by_type('PhSimpleContextSeg')
        """
        return self.by_type("PhSimpleContextSeg")

    def simple_context_nc(self):
        """
        Get only the simple natural class contexts.

        Convenience method for filtering to PhSimpleContextNC objects only.

        Returns:
            ContextCollection: New collection with only simple natural class contexts.

        Example::

            ncs = contexts.simple_context_nc()
            for nc_ctx in ncs:
                nc = nc_ctx.natural_class
                print(f"Natural Class: {nc}")

        Notes:
            - Simple natural class contexts represent a natural class
            - Equivalent to by_type('PhSimpleContextNC')
        """
        return self.by_type("PhSimpleContextNC")

    def complex_contexts(self):
        """
        Get only the complex contexts (segment or natural class).

        Convenience method for filtering to complex contexts (either
        PhComplexContextSeg or PhComplexContextNC).

        Returns:
            ContextCollection: New collection with only complex context objects.

        Example::

            complex = contexts.complex_contexts()
            print(f"Found {len(complex)} complex contexts")

            # Chain with other filters
            complex_word = contexts.complex_contexts().filter(name_contains='word')

        Notes:
            - Includes both PhComplexContextSeg and PhComplexContextNC
            - Use complex_context_seg() or complex_context_nc() to distinguish
        """
        filtered = [ctx for ctx in self._items if ctx.is_complex_context]
        return ContextCollection(filtered)

    def complex_context_seg(self):
        """
        Get only the complex segment contexts.

        Convenience method for filtering to PhComplexContextSeg objects only.

        Returns:
            ContextCollection: New collection with only complex segment contexts.

        Example::

            segs = contexts.complex_context_seg()
            print(f"Found {len(segs)} complex segment contexts")

        Notes:
            - Equivalent to by_type('PhComplexContextSeg')
            - Complex segment contexts have multiple segment specifications
        """
        return self.by_type("PhComplexContextSeg")

    def complex_context_nc(self):
        """
        Get only the complex natural class contexts.

        Convenience method for filtering to PhComplexContextNC objects only.

        Returns:
            ContextCollection: New collection with only complex natural class contexts.

        Example::

            ncs = contexts.complex_context_nc()
            print(f"Found {len(ncs)} complex natural class contexts")

        Notes:
            - Equivalent to by_type('PhComplexContextNC')
            - Complex natural class contexts have multiple natural class specifications
        """
        return self.by_type("PhComplexContextNC")

    def boundary_contexts(self):
        """
        Get only the boundary contexts.

        Convenience method for filtering to PhBoundaryContext objects only.

        Returns:
            ContextCollection: New collection with only boundary context objects.

        Example::

            boundaries = contexts.boundary_contexts()
            for bctx in boundaries:
                btype = bctx.boundary_type
                print(f"Boundary type: {btype}")

        Notes:
            - Boundary contexts represent word/morpheme boundaries
            - Equivalent to by_type('PhBoundaryContext')
        """
        return self.by_type("PhBoundaryContext")

    def __repr__(self):
        """Technical representation."""
        return f"ContextCollection({len(self._items)} contexts)"
