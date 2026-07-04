#
#   adhoc_prohibition.py
#
#   Class: AdhocProhibition
#          Wrapper for ad hoc morphosyntactic prohibition objects providing
#          unified interface access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Wrapper class for ad hoc morphosyntactic prohibition objects.

This module provides AdhocProhibition, a wrapper class that transparently
handles the three concrete types of morphosyntactic prohibitions:
- MoAdhocProhibGr: Grammatical feature prohibitions
- MoAdhocProhibMorph: Morpheme co-occurrence prohibitions
- MoAdhocProhibAllomorph: Allomorph co-occurrence prohibitions

The wrapper exposes a unified interface for accessing common properties
and provides convenience methods for checking type-specific capabilities
without exposing the underlying ClassName or casting complexity.

Problem:
    Morphosyntactic prohibitions have different properties depending on
    their concrete type:
    - MoAdhocProhibGr: Feature-based restrictions
    - MoAdhocProhibMorph: Morpheme-based restrictions
    - MoAdhocProhibAllomorph: Allomorph-based restrictions

    All have GUID and ClassName, but differ in restriction properties.

    Users working with mixed collections need to check ClassName and cast
    to access type-specific properties, which is error-prone and verbose.

Solution:
    AdhocProhibition wrapper provides:
    - Simple properties for common features (guid, prohibition_type)
    - Capability check properties (is_grammatical_prohibition, etc.)
    - Property access that works across all types
    - Human-readable description of the prohibition

Example::

    from flexlibs2.code.Grammar.adhoc_prohibition import AdhocProhibition

    # Wrap a prohibition from GetAllAdhocCoProhibitions()
    prohib = morphRuleOps.GetAllAdhocCoProhibitions()[0]
    wrapped = AdhocProhibition(prohib)

    # Access common properties
    print(wrapped.guid)  # Works for all prohibition types
    print(wrapped.prohibition_type)  # "Grammatical", "Morpheme", or "Allomorph"

    # Check capabilities
    if wrapped.is_morpheme_prohibition:
        # Access morpheme-specific properties
        morpheme = wrapped.MorphemeRA
        prohibited = wrapped.ProhibitedMorphemeRA

    # Optional: Advanced users can access concrete types
    if wrapped.as_morpheme_prohibition():
        concrete = wrapped.as_morpheme_prohibition()
        # Use concrete interface for advanced operations
"""

from ..Shared.wrapper_base import LCMObjectWrapper
from ..lcm_casting import cast_to_concrete


class AdhocProhibition(LCMObjectWrapper):
    """
    Wrapper for ad hoc morphosyntactic prohibition objects.

    Handles the three concrete types of prohibitions (MoAdhocProhibGr,
    MoAdhocProhibMorph, MoAdhocProhibAllomorph) transparently, providing
    common properties and capability checks without exposing ClassName
    or casting.

    Attributes:
        _obj: The base interface object (IMoAdhocProhib)
        _concrete: The concrete type object (IMoAdhocProhibGr,
                  IMoAdhocProhibMorph, or IMoAdhocProhibAllomorph)

    Example::

        prohib = morphRuleOps.GetAllAdhocCoProhibitions()[0]
        wrapped = AdhocProhibition(prohib)
        print(wrapped.prohibition_type)
        if wrapped.is_grammatical_prohibition:
            print("This is a grammatical feature prohibition")
    """

    def __init__(self, lcm_obj):
        """
        Initialize wrapper with an IMoAdhocProhib object.

        Args:
            lcm_obj: An IMoAdhocProhib object (or derived type).
                    Automatically casts to concrete type.

        Example::

            prohib = collection[0]
            wrapped = AdhocProhibition(prohib)
        """
        super().__init__(lcm_obj)

    @property
    def guid(self):
        """
        Get the GUID of this prohibition.

        Returns:
            str: The GUID as a string.

        Example::

            prohib_id = wrapped.guid
        """
        return str(self._obj.Guid)

    @property
    def prohibition_type(self):
        """
        Get a human-readable type identifier for this prohibition.

        Returns the prohibition type as a friendly string:
        - "Grammatical" for MoAdhocProhibGr
        - "Morpheme" for MoAdhocProhibMorph
        - "Allomorph" for MoAdhocProhibAllomorph
        - "Unknown" if type is not recognized

        Returns:
            str: Human-readable type name.

        Example::

            print(wrapped.prohibition_type)  # "Morpheme"
        """
        class_name = self.class_type

        if class_name == "MoAdhocProhibGr":
            return "Grammatical"
        elif class_name == "MoAdhocProhibMorph":
            return "Morpheme"
        elif class_name == "MoAdhocProhibAllomorph":
            return "Allomorph"
        else:
            return "Unknown"

    @property
    def is_grammatical_prohibition(self):
        """
        Check if this is a grammatical feature prohibition.

        Grammatical prohibitions restrict which feature values can combine.

        Returns:
            bool: True if this is a MoAdhocProhibGr, False otherwise.

        Example::

            if wrapped.is_grammatical_prohibition:
                feature = wrapped.FeatureRA
        """
        return self.class_type == "MoAdhocProhibGr"

    @property
    def is_morpheme_prohibition(self):
        """
        Check if this is a morpheme co-occurrence prohibition.

        Morpheme prohibitions restrict which morphemes can combine together.

        Returns:
            bool: True if this is a MoAdhocProhibMorph, False otherwise.

        Example::

            if wrapped.is_morpheme_prohibition:
                morph = wrapped.MorphemeRA
                prohibited = wrapped.ProhibitedMorphemeRA
        """
        return self.class_type == "MoAdhocProhibMorph"

    @property
    def is_allomorph_prohibition(self):
        """
        Check if this is an allomorph variant prohibition.

        Allomorph prohibitions restrict which allomorph variants can combine.

        Returns:
            bool: True if this is a MoAdhocProhibAllomorph, False otherwise.

        Example::

            if wrapped.is_allomorph_prohibition:
                allo = wrapped.AllomorphRA
                prohibited = wrapped.ProhibitedAllomorphRA
        """
        return self.class_type == "MoAdhocProhibAllomorph"

    def as_grammatical_prohibition(self):
        """
        Cast to grammatical prohibition type if applicable.

        For advanced users who need to access grammatical-specific properties
        directly via the C# interface.

        Returns:
            IMoAdhocProhibGr: The concrete interface if this is a grammatical
                prohibition, None otherwise.

        Example::

            concrete = wrapped.as_grammatical_prohibition()
            if concrete:
                feature = concrete.FeatureRA
                feature_value = concrete.FeatureValueRA
        """
        if self.is_grammatical_prohibition:
            return self._concrete
        return None

    def as_morpheme_prohibition(self):
        """
        Cast to morpheme prohibition type if applicable.

        For advanced users who need to access morpheme-specific properties
        directly via the C# interface.

        Returns:
            IMoAdhocProhibMorph: The concrete interface if this is a morpheme
                prohibition, None otherwise.

        Example::

            concrete = wrapped.as_morpheme_prohibition()
            if concrete:
                morpheme = concrete.MorphemeRA
                prohibited = concrete.ProhibitedMorphemeRA
        """
        if self.is_morpheme_prohibition:
            return self._concrete
        return None

    def as_allomorph_prohibition(self):
        """
        Cast to allomorph prohibition type if applicable.

        For advanced users who need to access allomorph-specific properties
        directly via the C# interface.

        Returns:
            IMoAdhocProhibAllomorph: The concrete interface if this is an
                allomorph prohibition, None otherwise.

        Example::

            concrete = wrapped.as_allomorph_prohibition()
            if concrete:
                allo = concrete.AllomorphRA
                prohibited = concrete.ProhibitedAllomorphRA
        """
        if self.is_allomorph_prohibition:
            return self._concrete
        return None

    def __repr__(self):
        """
        Technical representation showing prohibition type.

        Returns:
            str: Representation like "AdhocProhibition(MoAdhocProhibMorph)"
        """
        return f"{type(self).__name__}({self.class_type})"

    def __str__(self):
        """
        Human-readable string representation.

        Returns:
            str: Description like "Morpheme prohibition (uuid...)"
        """
        return f"{self.prohibition_type} prohibition ({self.guid[:8]}...)"
