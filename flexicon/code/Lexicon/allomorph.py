#
#   allomorph.py
#
#   Class: Allomorph
#          Wrapper for allomorph objects providing unified interface
#          access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Wrapper class for allomorph objects with unified interface.

This module provides Allomorph, a wrapper class that transparently
handles the two concrete types of allomorphs:
- MoStemAllomorph: Allomorphs of stems (StemName property)
- MoAffixAllomorph: Allomorphs of affixes (AffixType property)

The wrapper exposes a unified interface for accessing common properties
and provides convenience methods for checking type-specific capabilities
without exposing the underlying ClassName or casting complexity.

Problem:
    Allomorphs have different properties depending on their concrete type:
    - MoStemAllomorph has StemName property
    - MoAffixAllomorph has AffixType property

    Both have Form (ITsString), PhEnvironmentRC, Gloss, etc.

    Users working with mixed collections need to check ClassName and cast to
    access type-specific properties, which is error-prone and verbose.

Solution:
    Allomorph wrapper provides:
    - Simple properties for common features (form, environment, gloss)
    - Capability check properties (is_stem_allomorph, is_affix_allomorph)
    - Property access that works across all types
    - Optional: Methods for advanced users who know C# types

Example::

    from flexlibs2.code.Lexicon.allomorph import Allomorph

    # Wrap an allomorph from GetAll()
    allomorph = allomorphOps.GetAll(entry)[0]  # Typed as IMoForm
    wrapped = Allomorph(allomorph)

    # Access common properties
    print(wrapped.form)  # Works for all allomorph types
    print(wrapped.environment)

    # Check capabilities
    if wrapped.is_stem_allomorph:
        print("This is a stem allomorph")

    # Optional: Advanced users can access concrete types
    if wrapped.as_stem_allomorph():
        concrete = wrapped.as_stem_allomorph()
        # Use concrete interface for advanced operations
"""

from ..Shared.wrapper_base import LCMObjectWrapper
from ..lcm_casting import cast_to_concrete


class Allomorph(LCMObjectWrapper):
    """
    Wrapper for allomorph objects providing unified interface access.

    Handles the two concrete types of allomorphs (MoStemAllomorph,
    MoAffixAllomorph) transparently, providing common properties and
    capability checks without exposing ClassName or casting.

    Attributes:
        _obj: The base interface object (IMoForm)
        _concrete: The concrete type object (IMoStemAllomorph or IMoAffixAllomorph)

    Example::

        allomorph = allomorphOps.GetAll(entry)[0]
        wrapped = Allomorph(allomorph)
        print(wrapped.form)
        print(wrapped.environment)
        if wrapped.is_stem_allomorph:
            print("Stem allomorph")
    """

    def __init__(self, lcm_allomorph):
        """
        Initialize Allomorph wrapper with an allomorph object.

        Args:
            lcm_allomorph: An IMoForm object (or derived type).
                         Typically from AllomorphOperations.GetAll().

        Example::

            allomorph = allomorphOps.GetAll(entry)[0]
            wrapped = Allomorph(allomorph)
        """
        super().__init__(lcm_allomorph)

    # ========== Common Properties (work across all allomorph types) ==========

    @property
    def form(self) -> str:
        """
        Get the form (text) of this allomorph.

        Returns:
            str: The allomorph form, normalized and stripped of FLEx null markers.

        Example::

            print(f"Allomorph form: {wrapped.form}")
            # Output: "walk" or "-ing"

        Notes:
            - Uses vernacular writing system by default
            - Empty string returned if form not set
            - FLEx null marker ('***') is normalized to empty string
        """
        try:
            from SIL.LCModel.Core.KernelInterfaces import ITsString
            from ..Shared.string_utils import normalize_text

            form_multistring = self._obj.Form
            if form_multistring:
                # Get from default vernacular writing system
                default_ws = self._obj.Cache.DefaultVernWs
                form_text = ITsString(form_multistring.get_String(default_ws)).Text
                return normalize_text(form_text)
            return ""
        except Exception:
            return ""

    @property
    def gloss(self) -> str:
        """
        Get the gloss of this allomorph.

        Returns:
            str: The allomorph gloss, or empty string if not set.

        Example::

            if wrapped.gloss:
                print(f"Gloss: {wrapped.gloss}")

        Notes:
            - Gloss is typically empty for allomorphs (glosses go on senses)
            - This is included for completeness as allomorphs have Gloss field
        """
        try:
            from SIL.LCModel.Core.KernelInterfaces import ITsString
            from ..Shared.string_utils import normalize_text

            if hasattr(self._concrete, "Gloss") and self._concrete.Gloss:
                # Get from default analysis writing system
                default_ws = self._obj.Cache.DefaultAnalWs
                gloss_text = ITsString(self._concrete.Gloss.get_String(default_ws)).Text
                return normalize_text(gloss_text)
            return ""
        except Exception:
            return ""

    @property
    def environment(self) -> "list[object]":
        """
        Get the phonological environments for this allomorph.

        Returns:
            list: List of IPhEnvironment objects defining where this allomorph occurs.
                 Empty list if no environments specified (appears in all contexts).

        Example::

            for env in wrapped.environment:
                print(f"Environment: {env.Name}")

            if not wrapped.environment:
                print("This allomorph appears in all contexts")

        Notes:
            - Multiple environments use OR logic
            - Empty list means allomorph appears in any context
            - Environments guide the parser in selecting the appropriate allomorph
        """
        try:
            if hasattr(self._concrete, "PhoneEnvRC"):
                return list(self._concrete.PhoneEnvRC)
            return []
        except Exception:
            return []

    # ========== Type Detection Properties ==========

    @property
    def is_stem_allomorph(self):
        """
        Check if this is a stem allomorph.

        Returns:
            bool: True if this is a MoStemAllomorph, False otherwise.

        Example::

            if wrapped.is_stem_allomorph:
                print("This is a stem allomorph")
            else:
                print("This is an affix allomorph")

        Notes:
            - MoStemAllomorph allomorphs are variants of stems/roots
            - MoAffixAllomorph allomorphs are variants of affixes
        """
        try:
            return self.class_type == "MoStemAllomorph"
        except Exception:
            return False

    @property
    def is_affix_allomorph(self):
        """
        Check if this is an affix allomorph.

        Returns:
            bool: True if this is a MoAffixAllomorph, False otherwise.

        Example::

            if wrapped.is_affix_allomorph:
                print("This is an affix allomorph")
            else:
                print("This is a stem allomorph")

        Notes:
            - MoAffixAllomorph allomorphs are variants of prefixes, suffixes, etc.
            - MoStemAllomorph allomorphs are variants of stems/roots
        """
        try:
            return self.class_type == "MoAffixAllomorph"
        except Exception:
            return False

    # ========== Type-Specific Property Access ==========

    @property
    def stem_name(self):
        """
        Get the stem name (only for stem allomorphs).

        Returns:
            str: The stem name if this is a MoStemAllomorph, empty string otherwise.

        Example::

            if wrapped.is_stem_allomorph:
                print(f"Stem name: {wrapped.stem_name}")

        Notes:
            - Only available on MoStemAllomorph
            - Returns empty string for MoAffixAllomorph
            - StemName is a multistring property
        """
        if not self.is_stem_allomorph:
            return ""

        try:
            from SIL.LCModel.Core.KernelInterfaces import ITsString
            from ..Shared.string_utils import normalize_text

            if hasattr(self._concrete, "StemName") and self._concrete.StemName:
                # Get from default analysis writing system
                default_ws = self._obj.Cache.DefaultAnalWs
                stem_name_text = ITsString(self._concrete.StemName.get_String(default_ws)).Text
                return normalize_text(stem_name_text)
            return ""
        except Exception:
            return ""

    @property
    def affix_type(self):
        """
        Get the affix type (only for affix allomorphs).

        Returns:
            IMoMorphType or None: The affix type if this is a MoAffixAllomorph,
            None otherwise.

        Example::

            if wrapped.is_affix_allomorph and wrapped.affix_type:
                print(f"Affix type: {wrapped.affix_type.Name}")

        Notes:
            - Only available on MoAffixAllomorph
            - Returns None for MoStemAllomorph
            - AffixType indicates prefix, suffix, infix, etc.
        """
        if not self.is_affix_allomorph:
            return None

        try:
            if hasattr(self._concrete, "AffixType"):
                return self._concrete.AffixType
            return None
        except Exception:
            return None

    # ========== Advanced: Direct C# class access (optional for power users) ==========

    def as_stem_allomorph(self):
        """
        Cast to IMoStemAllomorph if this is a stem allomorph.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a MoStemAllomorph.

        Returns:
            IMoStemAllomorph or None: The concrete interface if this is a
                MoStemAllomorph, None otherwise.

        Example::

            if allomorph_obj.as_stem_allomorph():
                concrete = allomorph_obj.as_stem_allomorph()
                # Can now access IMoStemAllomorph-specific methods/properties
                stem_name = concrete.StemName
                # Advanced operations...

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_stem_allomorph and
              stem_name instead
            - Only useful if you need to call methods or access properties
              that aren't exposed through the wrapper
        """
        if self.class_type == "MoStemAllomorph":
            return self._concrete
        return None

    def as_affix_allomorph(self):
        """
        Cast to IMoAffixAllomorph if this is an affix allomorph.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a MoAffixAllomorph.

        Returns:
            IMoAffixAllomorph or None: The concrete interface if this is a
                MoAffixAllomorph, None otherwise.

        Example::

            if allomorph_obj.as_affix_allomorph():
                concrete = allomorph_obj.as_affix_allomorph()
                # Can now access IMoAffixAllomorph-specific methods/properties
                affix_type = concrete.AffixType
                # Advanced operations...

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_affix_allomorph and
              affix_type instead
        """
        if self.class_type == "MoAffixAllomorph":
            return self._concrete
        return None

    @property
    def concrete(self):
        """
        Get the raw concrete interface object.

        For advanced users who need to access the underlying C# interface
        directly without going through wrapper properties.

        Returns:
            The concrete interface object (IMoStemAllomorph or IMoAffixAllomorph
            depending on the allomorph's actual type).

        Example::

            # Direct access to concrete interface
            concrete = allomorph_obj.concrete
            stem_name = concrete.StemName  # MoStemAllomorph property

        Notes:
            - For power users only
            - Bypasses the wrapper's abstraction
            - Normal users should prefer wrapper properties like
              is_stem_allomorph, stem_name, etc.
        """
        return self._concrete

    def __repr__(self):
        """String representation showing allomorph form and type."""
        form = self.form or "Unnamed"
        return f"Allomorph({form}, {self.class_type})"

    def __str__(self):
        """Human-readable description."""
        form = self.form or "Unnamed"
        type_name = "Stem" if self.is_stem_allomorph else "Affix"
        return f"{type_name} Allomorph '{form}'"
