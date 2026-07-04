#
#   morphosyntax_analysis.py
#
#   Class: MorphosyntaxAnalysis
#          Wrapper for morphosyntactic analysis objects providing unified interface
#          access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Wrapper class for morphosyntactic analysis (MSA) objects with unified interface.

This module provides MorphosyntaxAnalysis, a wrapper class that transparently
handles the four concrete types of morphosyntactic analyses:
- MoStemMsa: Stem (root) analysis with Part of Speech
- MoDerivAffMsa: Derivational affix analysis with from/to Part of Speech
- MoInflAffMsa: Inflectional affix analysis with Part of Speech and slots
- MoUnclassifiedAffixMsa: Unclassified affix analysis

All share base interface IMoMorphSynAnalysis.

Problem:
    MSAs have different properties depending on their concrete type:
    - All have PartOfSpeechRA or similar properties for grammatical category
    - MoDerivAffMsa has FromPartOfSpeechRA and ToPartOfSpeechRA (input/output POS)
    - MoInflAffMsa has PartOfSpeechRA and inflection class references
    - Users working with mixed collections need to check ClassName and cast to
      access type-specific properties, which is error-prone and verbose.

Solution:
    MorphosyntaxAnalysis wrapper provides:
    - Simple properties for common features (pos_main, class_type)
    - Capability check properties (is_stem_msa, is_deriv_aff_msa, etc.)
    - Property access that works across all types
    - Optional: Methods for advanced users who know C# types

Example::

    from flexlibs2.code.Lexicon.morphosyntax_analysis import MorphosyntaxAnalysis

    # Wrap an MSA from entry.MorphoSyntaxAnalysesOC
    msa = entry.MorphoSyntaxAnalysesOC[0]
    wrapped = MorphosyntaxAnalysis(msa)

    # Access common properties
    if wrapped.is_stem_msa:
        print(f"Stem with POS: {wrapped.pos_main}")

    if wrapped.is_deriv_aff_msa:
        from_pos = wrapped.pos_from
        to_pos = wrapped.pos_to
        print(f"Derives: {from_pos} -> {to_pos}")

    # Check capabilities
    if wrapped.has_from_pos:
        print(f"From POS: {wrapped.pos_from}")

    # Optional: Advanced users can access concrete types
    if wrapped.as_stem_msa():
        concrete = wrapped.as_stem_msa()
        # Use concrete interface for advanced operations
"""

from ..Shared.wrapper_base import LCMObjectWrapper
from ..lcm_casting import cast_to_concrete, get_pos_from_msa, get_from_pos_from_msa


class MorphosyntaxAnalysis(LCMObjectWrapper):
    """
    Wrapper for morphosyntactic analysis objects providing unified interface access.

    Handles the four concrete types of MSAs (MoStemMsa, MoDerivAffMsa, MoInflAffMsa,
    MoUnclassifiedAffixMsa) transparently, providing common properties and capability
    checks without exposing ClassName or casting.

    Attributes:
        _obj: The base interface object (IMoMorphSynAnalysis)
        _concrete: The concrete type object (IMoStemMsa, IMoDerivAffMsa,
                  IMoInflAffMsa, or IMoUnclassifiedAffixMsa)

    Example::

        msa = entry.MorphoSyntaxAnalysesOC[0]
        wrapped = MorphosyntaxAnalysis(msa)
        print(wrapped.class_type)
        if wrapped.is_stem_msa:
            print(wrapped.pos_main)
    """

    def __init__(self, lcm_msa):
        """
        Initialize MorphosyntaxAnalysis wrapper with an MSA object.

        Args:
            lcm_msa: An IMoMorphSynAnalysis object (or derived type).
                     Typically from entry.MorphoSyntaxAnalysesOC.

        Example::

            msa = entry.MorphoSyntaxAnalysesOC[0]
            wrapped = MorphosyntaxAnalysis(msa)
        """
        super().__init__(lcm_msa)

    # ========== Type Check Properties ==========

    @property
    def is_stem_msa(self):
        """
        Check if this is a stem MSA (MoStemMsa).

        Returns:
            bool: True if this is a MoStemMsa object.

        Example::

            if wrapped.is_stem_msa:
                pos = wrapped.pos_main
                print(f"Stem POS: {pos}")
        """
        return self.class_type == "MoStemMsa"

    @property
    def is_deriv_aff_msa(self):
        """
        Check if this is a derivational affix MSA (MoDerivAffMsa).

        Returns:
            bool: True if this is a MoDerivAffMsa object.

        Example::

            if wrapped.is_deriv_aff_msa:
                from_pos = wrapped.pos_from
                to_pos = wrapped.pos_to
                print(f"Derives: {from_pos} -> {to_pos}")
        """
        return self.class_type == "MoDerivAffMsa"

    @property
    def is_infl_aff_msa(self):
        """
        Check if this is an inflectional affix MSA (MoInflAffMsa).

        Returns:
            bool: True if this is a MoInflAffMsa object.

        Example::

            if wrapped.is_infl_aff_msa:
                pos = wrapped.pos_main
                print(f"Inflectional affix for POS: {pos}")
        """
        return self.class_type == "MoInflAffMsa"

    @property
    def is_unclassified_aff_msa(self):
        """
        Check if this is an unclassified affix MSA (MoUnclassifiedAffixMsa).

        Returns:
            bool: True if this is a MoUnclassifiedAffixMsa object.

        Example::

            if wrapped.is_unclassified_aff_msa:
                pos = wrapped.pos_main
                print(f"Unclassified affix with POS: {pos}")
        """
        return self.class_type == "MoUnclassifiedAffixMsa"

    # ========== Common Properties (work across most MSA types) ==========

    @property
    def pos_main(self):
        """
        Get the main Part of Speech for this MSA.

        Returns the PartOfSpeechRA for stem and inflectional affixes,
        and ToPartOfSpeechRA for derivational affixes (output POS).

        Returns:
            IPartOfSpeech or None: The main POS reference, or None if not set.

        Example::

            if wrapped.pos_main:
                pos_name = wrapped.pos_main.Name.BestAnalysisAlternative.Text
                print(f"POS: {pos_name}")

        Notes:
            - For MoStemMsa, MoInflAffMsa, MoUnclassifiedAffixMsa: PartOfSpeechRA
            - For MoDerivAffMsa: ToPartOfSpeechRA (output POS)
            - Use pos_from for derivational affix input POS
        """
        return get_pos_from_msa(self._obj)

    @property
    def has_from_pos(self):
        """
        Check if this MSA has a "from" Part of Speech (input POS).

        Only meaningful for derivational affixes, which show what POS
        something derives from. Returns False for all other MSA types.

        Returns:
            bool: True if this is a MoDerivAffMsa with FromPartOfSpeechRA set.

        Example::

            if wrapped.has_from_pos:
                from_pos = wrapped.pos_from
                to_pos = wrapped.pos_to
                print(f"Derives: {from_pos} -> {to_pos}")

        Notes:
            - Only MoDerivAffMsa has FromPartOfSpeechRA
            - Always False for MoStemMsa, MoInflAffMsa, MoUnclassifiedAffixMsa
        """
        if not self.is_deriv_aff_msa:
            return False

        try:
            return get_from_pos_from_msa(self._obj) is not None
        except Exception:
            return False

    @property
    def pos_from(self):
        """
        Get the "from" Part of Speech for derivational affixes.

        Only meaningful for MoDerivAffMsa. Shows the POS before derivation.
        Returns None for all other MSA types.

        Returns:
            IPartOfSpeech or None: The input POS for derivational affixes,
                or None if not a derivational affix or not set.

        Example::

            if wrapped.has_from_pos:
                from_pos = wrapped.pos_from
                to_pos = wrapped.pos_to
                print(f"Derives {from_pos.Name} to {to_pos.Name}")

        Notes:
            - Only meaningful for MoDerivAffMsa
            - Returns None for MoStemMsa, MoInflAffMsa, MoUnclassifiedAffixMsa
            - Use pos_to to get the output POS
        """
        if not self.is_deriv_aff_msa:
            return None

        return get_from_pos_from_msa(self._obj)

    @property
    def pos_to(self):
        """
        Get the "to" Part of Speech for derivational affixes.

        For derivational affixes, this is the output POS (what you get after
        applying the derivation). For other MSA types, returns the same as pos_main.

        Returns:
            IPartOfSpeech or None: The output POS for derivational affixes,
                or the main POS for other types, or None if not set.

        Example::

            if wrapped.is_deriv_aff_msa:
                from_pos = wrapped.pos_from
                to_pos = wrapped.pos_to
                print(f"Change: {from_pos} -> {to_pos}")

        Notes:
            - For MoDerivAffMsa: ToPartOfSpeechRA (output after derivation)
            - For other types: Same as pos_main
        """
        if self.is_deriv_aff_msa:
            return get_pos_from_msa(self._obj)  # ToPartOfSpeechRA
        else:
            return self.pos_main

    # ========== Advanced: Direct C# class access (optional for power users) ==========

    def as_stem_msa(self):
        """
        Cast to IMoStemMsa if this is a stem MSA.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a MoStemMsa.

        Returns:
            IMoStemMsa or None: The concrete interface if this is a
                MoStemMsa, None otherwise.

        Example::

            if wrapped.as_stem_msa():
                concrete = wrapped.as_stem_msa()
                # Can now access IMoStemMsa-specific methods/properties
                # Advanced operations...

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like pos_main instead
            - Only useful if you need to call methods or access properties
              that aren't exposed through the wrapper
        """
        if self.class_type == "MoStemMsa":
            return self._concrete
        return None

    def as_deriv_aff_msa(self):
        """
        Cast to IMoDerivAffMsa if this is a derivational affix MSA.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a MoDerivAffMsa.

        Returns:
            IMoDerivAffMsa or None: The concrete interface if this is a
                MoDerivAffMsa, None otherwise.

        Example::

            if wrapped.as_deriv_aff_msa():
                concrete = wrapped.as_deriv_aff_msa()
                # Can now access IMoDerivAffMsa-specific methods/properties

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like pos_from and pos_to instead
        """
        if self.class_type == "MoDerivAffMsa":
            return self._concrete
        return None

    def as_infl_aff_msa(self):
        """
        Cast to IMoInflAffMsa if this is an inflectional affix MSA.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a MoInflAffMsa.

        Returns:
            IMoInflAffMsa or None: The concrete interface if this is a
                MoInflAffMsa, None otherwise.

        Example::

            if wrapped.as_infl_aff_msa():
                concrete = wrapped.as_infl_aff_msa()
                # Can now access IMoInflAffMsa-specific methods/properties

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like pos_main instead
        """
        if self.class_type == "MoInflAffMsa":
            return self._concrete
        return None

    def as_unclassified_aff_msa(self):
        """
        Cast to IMoUnclassifiedAffixMsa if this is an unclassified affix MSA.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a MoUnclassifiedAffixMsa.

        Returns:
            IMoUnclassifiedAffixMsa or None: The concrete interface if this is a
                MoUnclassifiedAffixMsa, None otherwise.

        Example::

            if wrapped.as_unclassified_aff_msa():
                concrete = wrapped.as_unclassified_aff_msa()
                # Can now access IMoUnclassifiedAffixMsa-specific methods/properties

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like pos_main instead
        """
        if self.class_type == "MoUnclassifiedAffixMsa":
            return self._concrete
        return None

    @property
    def concrete(self):
        """
        Get the raw concrete interface object.

        For advanced users who need to access the underlying C# interface
        directly without going through wrapper properties.

        Returns:
            The concrete interface object (IMoStemMsa, IMoDerivAffMsa,
            IMoInflAffMsa, or IMoUnclassifiedAffixMsa depending on the MSA's
            actual type).

        Example::

            # Direct access to concrete interface
            concrete = msa_obj.concrete
            pos = concrete.PartOfSpeechRA  # MSA type-specific property

        Notes:
            - For power users only
            - Bypasses the wrapper's abstraction
            - Normal users should prefer wrapper properties like
              is_stem_msa, pos_main, etc.
        """
        return self._concrete

    def __repr__(self):
        """String representation showing MSA type."""
        return f"MorphosyntaxAnalysis({self.class_type})"

    def __str__(self):
        """Human-readable description."""
        pos = self.pos_main
        pos_name = ""
        if pos:
            try:
                pos_name = f" [{pos.Name.BestAnalysisAlternative.Text}]"
            except Exception:
                pos_name = " [unknown POS]"

        return f"{self.class_type}{pos_name}"
