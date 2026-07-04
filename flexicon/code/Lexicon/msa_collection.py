#
#   msa_collection.py
#
#   Class: MSACollection
#          Smart collection for morphosyntactic analyses with type-aware filtering
#          and unified access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Smart collection class for morphosyntactic analyses.

This module provides MSACollection, a smart collection that manages
morphosyntactic analyses while showing type diversity and supporting unified
operations across the four concrete types:
- MoStemMsa
- MoDerivAffMsa
- MoInflAffMsa
- MoUnclassifiedAffixMsa

Problem:
    entry.MorphoSyntaxAnalysesOC returns objects with multiple concrete
    implementations. Users need to:
    - See which types are in the collection
    - Filter by type if they want to
    - Work with all types together without manual casting
    - Filter by common properties that work across all types

Solution:
    MSACollection provides:
    - __str__() showing type breakdown
    - by_type() filtering to specific concrete types
    - filter() for common criteria (pos_main, has_pos, where_predicate)
    - Convenience methods (stem_msas(), deriv_aff_msas(), infl_aff_msas(),
      unclassified_aff_msas())
    - Chainable filtering: msas.stem_msas().filter(pos_main=some_pos)

Example::

    from flexlibs2.code.Lexicon.msa_collection import MSACollection

    # entry.MorphoSyntaxAnalysesOC already wrapped by LexEntryOperations
    msas = entry_ops.GetMorphoSyntaxAnalyses(entry)
    print(msas)  # Shows type breakdown
    # MSACollection (8 total)
    #   MoStemMsa: 4 (50%)
    #   MoDerivAffMsa: 2 (25%)
    #   MoInflAffMsa: 2 (25%)

    # Filter by type
    stem_only = msas.stem_msas()
    print(len(stem_only))  # 4

    # Filter by POS
    target_pos = ...
    matching = msas.filter(pos_main=target_pos)

    # Chain filters
    stem_with_pos = msas.stem_msas().filter(pos_main=target_pos)

    # Iterate
    for msa in msas:
        print(msa.class_type)
"""

from ..Shared.smart_collection import SmartCollection
from .morphosyntax_analysis import MorphosyntaxAnalysis


class MSACollection(SmartCollection):
    """
    Smart collection for morphosyntactic analyses with type-aware filtering.

    Manages collections of morphosyntactic analysis objects (MorphosyntaxAnalysis
    wrapper objects) with type-aware display and filtering capabilities. Supports
    filtering by common properties (POS, has_pos) and by concrete type.

    Attributes:
        _items: List of MorphosyntaxAnalysis wrapper objects

    Example::

        msas = entry_ops.GetMorphoSyntaxAnalyses(entry)
        print(msas)  # Shows type breakdown
        stem = msas.stem_msas()  # Filter to MoStemMsa
        with_pos = msas.filter(pos_main=target_pos)  # POS filter
        both = msas.stem_msas().filter(pos_main=target_pos)  # Chain
    """

    def __init__(self, items=None):
        """
        Initialize an MSACollection.

        Args:
            items: Iterable of MorphosyntaxAnalysis objects, or None for empty.

        Example::

            collection = MSACollection()
            collection = MSACollection([msa1, msa2, msa3])
        """
        super().__init__(items)

    def filter(self, pos_main=None, has_pos=None, where=None):
        """
        Filter the collection by common MSA properties.

        Supports filtering by properties that work across all MSA types
        (pos_main, has_pos). For complex filtering, use where().

        Args:
            pos_main (IPartOfSpeech, optional): Filter to MSAs with this
                Part of Speech (uses GUID comparison). For derivational
                affixes, this filters by ToPartOfSpeechRA.
            has_pos (bool, optional): If True, only include MSAs with a
                pos_main set. If False, only include MSAs without pos_main.
            where (callable, optional): Custom predicate function. If provided,
                other criteria are ignored.

        Returns:
            MSACollection: New collection with filtered items.

        Example::

            # Filter by POS
            target_pos = ...
            matching = msas.filter(pos_main=target_pos)

            # Filter by presence of POS
            with_pos = msas.filter(has_pos=True)
            without_pos = msas.filter(has_pos=False)

            # Custom filtering
            deriv_with_pos = msas.where(
                lambda m: m.is_deriv_aff_msa and m.has_from_pos
            )

            # Chain filters
            stem_with_pos = msas.stem_msas().filter(pos_main=target_pos)

        Notes:
            - pos_main comparison uses GUID string comparison
            - has_pos and pos_main filters are AND-ed together
            - where() takes precedence over other criteria
            - Returns new collection (doesn't modify original)
            - Use where() for complex custom filtering
        """
        # If custom predicate provided, use it
        if where is not None:
            filtered = [item for item in self._items if where(item)]
            return MSACollection(filtered)

        # Apply criteria filters
        filtered = self._items

        if has_pos is not None:
            if has_pos:
                # Include only MSAs with pos_main set
                filtered = [msa for msa in filtered if msa.pos_main is not None]
            else:
                # Include only MSAs without pos_main
                filtered = [msa for msa in filtered if msa.pos_main is None]

        if pos_main is not None:
            # Get the GUID of the target POS for comparison
            target_guid = None
            if hasattr(pos_main, "Guid"):
                target_guid = str(pos_main.Guid)
            else:
                target_guid = str(pos_main)

            filtered = [msa for msa in filtered if msa.pos_main is not None and str(msa.pos_main.Guid) == target_guid]

        return MSACollection(filtered)

    def where(self, predicate):
        """
        Filter using a custom predicate function.

        For filtering by complex criteria or properties not supported by filter().

        Args:
            predicate (callable): Function that takes a MorphosyntaxAnalysis and
                returns True to include it in the result.

        Returns:
            MSACollection: New collection with items matching the predicate.

        Example::

            # Complex predicate: derivational affixes with from/to POS
            deriv_with_both = msas.where(
                lambda m: m.is_deriv_aff_msa and
                          m.pos_from is not None and
                          m.pos_to is not None
            )

            # Combining conditions
            specific = msas.where(
                lambda m: m.is_stem_msa and m.pos_main is not None
            )

            # Type checking combined with other criteria
            non_stem = msas.where(lambda m: not m.is_stem_msa)

        Notes:
            - Predicate receives each MorphosyntaxAnalysis object
            - Return True to include in result, False to exclude
            - For simple filters (pos_main, has_pos), use filter() instead
        """
        filtered = [msa for msa in self._items if predicate(msa)]
        return MSACollection(filtered)

    def stem_msas(self):
        """
        Get only the stem (MoStemMsa) MSAs from the collection.

        Convenience method for filtering to MoStemMsa objects only.

        Returns:
            MSACollection: New collection with only MoStemMsa objects.

        Example::

            stem = msas.stem_msas()
            print(f"Found {len(stem)} stem MSAs")

            # Chain with other filters
            stem_with_pos = msas.stem_msas().filter(has_pos=True)

        Notes:
            - Equivalent to by_type('MoStemMsa')
            - Stem MSAs have PartOfSpeechRA for the main POS
            - Use is_stem_msa on individual MSAs to check type
        """
        return self.by_type("MoStemMsa")

    def deriv_aff_msas(self):
        """
        Get only the derivational affix (MoDerivAffMsa) MSAs from the collection.

        Convenience method for filtering to MoDerivAffMsa objects only.

        Returns:
            MSACollection: New collection with only MoDerivAffMsa objects.

        Example::

            deriv = msas.deriv_aff_msas()
            print(f"Found {len(deriv)} derivational affix MSAs")

            # Chain with other filters
            deriv_with_from = msas.deriv_aff_msas().filter(has_pos=True)

        Notes:
            - Equivalent to by_type('MoDerivAffMsa')
            - Derivational affixes have FromPartOfSpeechRA and ToPartOfSpeechRA
            - Use is_deriv_aff_msa on individual MSAs to check type
        """
        return self.by_type("MoDerivAffMsa")

    def infl_aff_msas(self):
        """
        Get only the inflectional affix (MoInflAffMsa) MSAs from the collection.

        Convenience method for filtering to MoInflAffMsa objects only.

        Returns:
            MSACollection: New collection with only MoInflAffMsa objects.

        Example::

            infl = msas.infl_aff_msas()
            print(f"Found {len(infl)} inflectional affix MSAs")

            # Chain with other filters
            infl_with_pos = msas.infl_aff_msas().filter(has_pos=True)

        Notes:
            - Equivalent to by_type('MoInflAffMsa')
            - Inflectional affixes have PartOfSpeechRA and slot references
            - Use is_infl_aff_msa on individual MSAs to check type
        """
        return self.by_type("MoInflAffMsa")

    def unclassified_aff_msas(self):
        """
        Get only the unclassified affix (MoUnclassifiedAffixMsa) MSAs from the collection.

        Convenience method for filtering to MoUnclassifiedAffixMsa objects only.

        Returns:
            MSACollection: New collection with only MoUnclassifiedAffixMsa objects.

        Example::

            unclass = msas.unclassified_aff_msas()
            print(f"Found {len(unclass)} unclassified affix MSAs")

            # Chain with other filters
            unclass_with_pos = msas.unclassified_aff_msas().filter(has_pos=True)

        Notes:
            - Equivalent to by_type('MoUnclassifiedAffixMsa')
            - Unclassified affixes have PartOfSpeechRA
            - Use is_unclassified_aff_msa on individual MSAs to check type
        """
        return self.by_type("MoUnclassifiedAffixMsa")

    def __repr__(self):
        """Technical representation."""
        return f"MSACollection({len(self._items)} items)"
