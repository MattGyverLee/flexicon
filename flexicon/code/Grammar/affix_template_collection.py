#
#   affix_template_collection.py
#
#   Class: AffixTemplateCollection
#          Smart collection for affix templates with type-aware filtering
#          and unified access across templates.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Smart collection class for affix templates.

This module provides AffixTemplateCollection, a smart collection that manages
affix templates while supporting unified operations and convenient filtering.

Problem:
    GetAll() returns multiple templates from different parts of speech.
    Users need to:
    - See how many templates are in the collection
    - Filter by common criteria (name, stratum, slot availability)
    - Work with templates without manual casting or checking

Solution:
    AffixTemplateCollection provides:
    - __str__() showing template summary
    - filter() for common criteria (name_contains, stratum)
    - Convenience methods (with_prefix_slots, with_suffix_slots, etc.)
    - Chainable filtering: templates.with_prefix_slots().filter(name_contains='Verb')
    - where() for custom predicates

Example::

    from flexlibs2.code.Grammar.affix_template_collection import AffixTemplateCollection

    # GetAll() now returns AffixTemplateCollection
    templates = morphRuleOps.GetAllAffixTemplates()
    print(templates)  # Shows collection summary

    # Filter by slots
    prefix_templates = templates.with_prefix_slots()
    print(f"Templates with prefix slots: {len(prefix_templates)}")

    # Filter by name
    verb_templates = templates.filter(name_contains='Verb')

    # Chain filters
    verb_prefix = templates.with_prefix_slots().filter(name_contains='Verb')

    # Iterate
    for template in templates:
        print(template.name)
"""

from ..Shared.smart_collection import SmartCollection
from .affix_template import AffixTemplate


class AffixTemplateCollection(SmartCollection):
    """
    Smart collection for affix templates with filtering capabilities.

    Manages collections of affix templates (AffixTemplate wrapper objects)
    with type-aware display and filtering capabilities. Supports filtering by
    common properties (name, stratum, slot availability).

    Attributes:
        _items: List of AffixTemplate wrapper objects

    Example::

        templates = morphRuleOps.GetAllAffixTemplates()
        print(templates)  # Shows collection summary
        prefix = templates.with_prefix_slots()  # Filter to templates with prefixes
        verb = templates.filter(name_contains='Verb')  # Name filter
        both = templates.with_prefix_slots().filter(name_contains='Verb')  # Chain
    """

    def __init__(self, items=None):
        """
        Initialize an AffixTemplateCollection.

        Args:
            items: Iterable of AffixTemplate objects, or None for empty.

        Example::

            collection = AffixTemplateCollection()
            collection = AffixTemplateCollection([template1, template2, template3])
        """
        super().__init__(items)

    def filter(self, name_contains=None, stratum=None, where=None):
        """
        Filter the collection by common template properties.

        Supports filtering by properties that work across all templates
        (name, stratum). For complex filtering, use where().

        Args:
            name_contains (str, optional): Filter to templates whose name contains
                this string (case-sensitive).
            stratum (str, optional): Filter by stratum name or reference.
            where (callable, optional): Custom predicate function. If provided,
                other criteria are ignored.

        Returns:
            AffixTemplateCollection: New collection with filtered items.

        Example::

            # Filter by name
            verb_templates = templates.filter(name_contains='Verb')

            # Filter by stratum
            stratum1 = templates.filter(stratum='Stratum1')

            # Custom filtering
            with_slots = templates.where(lambda t: t.has_any_slots)

            # Chain filters
            verb_stratum = templates.filter(name_contains='Verb').filter(stratum='Stratum1')

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
            return AffixTemplateCollection(filtered)

        # Apply criteria filters
        filtered = self._items

        if name_contains is not None:
            filtered = [template for template in filtered if name_contains in (template.name or "")]

        if stratum is not None:
            filtered = [
                template
                for template in filtered
                if template.stratum
                and (stratum in (template.stratum.Name or "") or str(stratum) == str(template.stratum))
            ]

        return AffixTemplateCollection(filtered)

    def where(self, predicate):
        """
        Filter using a custom predicate function.

        For filtering by complex criteria or properties not supported by filter().

        Args:
            predicate (callable): Function that takes an AffixTemplate and
                returns True to include it in the result.

        Returns:
            AffixTemplateCollection: New collection with items matching the predicate.

        Example::

            # Complex predicate: templates with both prefix and suffix slots
            full_templates = templates.where(
                lambda t: t.has_prefix_slots and t.has_suffix_slots
            )

            # Combining conditions
            complex_filter = templates.where(
                lambda t: t.has_any_slots and (t.name or "").startswith('Verb')
            )

            # Capability checking
            prefix_templates = templates.where(lambda t: t.has_prefix_slots)

        Notes:
            - Predicate receives each AffixTemplate object
            - Return True to include in result, False to exclude
            - For simple filters (name, stratum), use filter() instead
        """
        filtered = [template for template in self._items if predicate(template)]
        return AffixTemplateCollection(filtered)

    def with_prefix_slots(self):
        """
        Get only the templates that have prefix slots.

        Convenience method for filtering to templates with prefix slots.

        Returns:
            AffixTemplateCollection: New collection with templates that have prefix slots.

        Example::

            prefix_templates = templates.with_prefix_slots()
            print(f"Found {len(prefix_templates)} templates with prefix slots")

            # Chain with other filters
            verb_prefix = templates.with_prefix_slots().filter(name_contains='Verb')

        Notes:
            - Equivalent to where(lambda t: t.has_prefix_slots)
            - Use has_prefix_slots on individual templates to check
        """
        return self.where(lambda t: t.has_prefix_slots)

    def with_suffix_slots(self):
        """
        Get only the templates that have suffix slots.

        Convenience method for filtering to templates with suffix slots.

        Returns:
            AffixTemplateCollection: New collection with templates that have suffix slots.

        Example::

            suffix_templates = templates.with_suffix_slots()
            print(f"Found {len(suffix_templates)} templates with suffix slots")

            # Chain with other filters
            verb_suffix = templates.with_suffix_slots().filter(name_contains='Verb')

        Notes:
            - Equivalent to where(lambda t: t.has_suffix_slots)
            - Use has_suffix_slots on individual templates to check
        """
        return self.where(lambda t: t.has_suffix_slots)

    def with_proclitic_slots(self):
        """
        Get only the templates that have proclitic slots.

        Convenience method for filtering to templates with proclitic slots.

        Returns:
            AffixTemplateCollection: New collection with templates that have proclitic slots.

        Example::

            proclitic_templates = templates.with_proclitic_slots()
            print(f"Found {len(proclitic_templates)} templates with proclitic slots")

        Notes:
            - Equivalent to where(lambda t: t.has_proclitic_slots)
            - Use has_proclitic_slots on individual templates to check
        """
        return self.where(lambda t: t.has_proclitic_slots)

    def with_enclitic_slots(self):
        """
        Get only the templates that have enclitic slots.

        Convenience method for filtering to templates with enclitic slots.

        Returns:
            AffixTemplateCollection: New collection with templates that have enclitic slots.

        Example::

            enclitic_templates = templates.with_enclitic_slots()
            print(f"Found {len(enclitic_templates)} templates with enclitic slots")

        Notes:
            - Equivalent to where(lambda t: t.has_enclitic_slots)
            - Use has_enclitic_slots on individual templates to check
        """
        return self.where(lambda t: t.has_enclitic_slots)

    def with_slots(self, slot_type):
        """
        Get only the templates that have slots of a specific type.

        Convenience method for filtering to specific slot types.

        Args:
            slot_type (str): Type of slots to filter by:
                'prefix', 'suffix', 'proclitic', or 'enclitic'.

        Returns:
            AffixTemplateCollection: New collection with templates that have the specified slots.

        Example::

            # Get templates with prefix slots
            prefix_templates = templates.with_slots('prefix')

            # Get templates with suffix slots
            suffix_templates = templates.with_slots('suffix')

            # Get templates with proclitic slots
            proclitic_templates = templates.with_slots('proclitic')

        Notes:
            - slot_type must be one of: 'prefix', 'suffix', 'proclitic', 'enclitic'
            - Returns empty collection if slot_type is not recognized
        """
        slot_type = (slot_type or "").lower()
        if slot_type == "prefix":
            return self.with_prefix_slots()
        elif slot_type == "suffix":
            return self.with_suffix_slots()
        elif slot_type == "proclitic":
            return self.with_proclitic_slots()
        elif slot_type == "enclitic":
            return self.with_enclitic_slots()
        else:
            # Unrecognized slot type, return empty collection
            return AffixTemplateCollection([])

    def with_any_slots(self):
        """
        Get only the templates that have any slots.

        Convenience method for filtering to templates with at least one slot.

        Returns:
            AffixTemplateCollection: New collection with templates that have slots.

        Example::

            templates_with_slots = templates.with_any_slots()
            print(f"Found {len(templates_with_slots)} templates with slots")

        Notes:
            - Equivalent to where(lambda t: t.has_any_slots)
        """
        return self.where(lambda t: t.has_any_slots)

    def full_templates(self):
        """
        Get only the templates that have all four slot types.

        Convenience method for filtering to templates with prefix, suffix,
        proclitic, and enclitic slots.

        Returns:
            AffixTemplateCollection: New collection with full-featured templates.

        Example::

            full_templates = templates.full_templates()
            print(f"Found {len(full_templates)} templates with all slot types")

        Notes:
            - Equivalent to where(lambda t: all([
                    t.has_prefix_slots,
                    t.has_suffix_slots,
                    t.has_proclitic_slots,
                    t.has_enclitic_slots
                ]))
        """
        return self.where(
            lambda t: (t.has_prefix_slots and t.has_suffix_slots and t.has_proclitic_slots and t.has_enclitic_slots)
        )

    def for_pos(self, pos_name_or_object):
        """
        Get only the templates for a specific part of speech.

        Convenience method for filtering templates by their owner POS.

        Args:
            pos_name_or_object: Either a POS name (str) or a POS object.

        Returns:
            AffixTemplateCollection: New collection with templates for the specified POS.

        Example::

            # Filter by POS name
            verb_templates = templates.for_pos('Verb')

            # Filter by POS object
            verb_pos = posOps.Find('Verb')
            verb_templates = templates.for_pos(verb_pos)

        Notes:
            - If pos_name_or_object is a string, looks for POS names containing the string
            - Returns empty collection if no templates found for the POS
        """
        if isinstance(pos_name_or_object, str):
            pos_name = pos_name_or_object
            return self.where(lambda t: t.owner_pos and pos_name in (t.owner_pos.Name or ""))
        else:
            pos_obj = pos_name_or_object
            return self.where(lambda t: t.owner_pos and t.owner_pos == pos_obj)

    def __repr__(self):
        """Technical representation."""
        return f"AffixTemplateCollection({len(self._items)} templates)"
