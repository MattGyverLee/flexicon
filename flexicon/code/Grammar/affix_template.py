#
#   affix_template.py
#
#   Class: AffixTemplate
#          Wrapper for affix template objects providing unified interface
#          access to template properties and slots.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Wrapper class for affix template objects with unified interface.

This module provides AffixTemplate, a wrapper class that transparently
handles affix template objects (MoInflAffixTemplate) providing convenient
access to template properties and slots.

Problem:
    Affix templates contain multiple slot collections and properties that
    require navigation through the LCM object hierarchy. Users working with
    templates need convenient access to:
    - Basic properties (name, description, stratum, disabled)
    - Slot collections (prefix, suffix, proclitic, enclitic)
    - Convenience properties (slot counts, capabilities)

Solution:
    AffixTemplate wrapper provides:
    - Simple properties for common features (name, description, stratum)
    - Direct access to slot collections
    - Convenience properties for slot counts and checks
    - Capability check properties (has_prefix_slots, etc.)
    - Property access that works transparently

Example::

    from flexlibs2.code.Grammar.affix_template import AffixTemplate

    # Wrap a template from GetAll()
    template = morphRuleOps.GetAllAffixTemplates()[0]
    wrapped = AffixTemplate(template)

    # Access common properties
    print(wrapped.name)  # Template name
    print(wrapped.description)  # Template description
    print(wrapped.stratum)  # Stratum reference

    # Check capabilities
    if wrapped.has_prefix_slots:
        print(f"Template has {wrapped.prefix_slot_count} prefix slots")

    # Access slots directly
    for slot in wrapped.prefix_slots:
        print(f"Slot: {slot.Name}")
"""

from ..Shared.wrapper_base import LCMObjectWrapper
from ..lcm_casting import cast_to_concrete

try:
    from SIL.LCModel import IPartOfSpeech, PartOfSpeechTags
except ImportError:
    # Mock for testing without FieldWorks installed
    IPartOfSpeech = None
    class PartOfSpeechTags:
        kClassId = 0


class AffixTemplate(LCMObjectWrapper):
    """
    Wrapper for affix template objects providing unified interface access.

    Handles MoInflAffixTemplate objects transparently, providing common
    properties and convenience methods without exposing ClassName or casting.

    Attributes:
        _obj: The base interface object (IMoInflAffixTemplate)
        _concrete: The concrete type object (IMoInflAffixTemplate)

    Example::

        template = morphRuleOps.GetAllAffixTemplates()[0]
        wrapped = AffixTemplate(template)
        print(wrapped.name)
        print(wrapped.prefix_slot_count)
        if wrapped.has_suffix_slots:
            print(f"Has {wrapped.suffix_slot_count} suffix slots")
    """

    def __init__(self, lcm_template):
        """
        Initialize AffixTemplate wrapper with a template object.

        Args:
            lcm_template: An IMoInflAffixTemplate object.
                         Typically from MorphRuleOperations.GetAllAffixTemplates().

        Example::

            template = morphRuleOps.GetAllAffixTemplates()[0]
            wrapped = AffixTemplate(template)
        """
        super().__init__(lcm_template)

    # ========== Common Properties (basic template information) ==========

    @property
    def name(self) -> str:
        """
        Get the template's name.

        Returns:
            str: The template name, or empty string if not set.

        Example::

            print(f"Template: {wrapped.name}")
        """
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        name_multistring = self._obj.Name
        if not name_multistring:
            return ""
        default_ws = self._obj.Cache.DefaultAnalWs
        name_text = ITsString(name_multistring.get_String(default_ws)).Text
        return name_text or ""

    @property
    def description(self):
        """
        Get the template's description.

        Returns:
            str: The template description, or empty string if not set.

        Example::

            print(f"Description: {wrapped.description}")
        """
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        desc_multistring = self._obj.Description
        if not desc_multistring:
            return ""
        default_ws = self._obj.Cache.DefaultAnalWs
        desc_text = ITsString(desc_multistring.get_String(default_ws)).Text
        return desc_text or ""

    @property
    def stratum(self):
        """
        Get the template's stratum reference.

        Returns:
            IMoStratum or None: The phonological stratum that owns this template, or None if not set.

        Example::

            if wrapped.stratum:
                print(f"Stratum: {wrapped.stratum.Name}")
        """
        try:
            if hasattr(self._concrete, "StratumRA"):
                return self._concrete.StratumRA
            return None
        except Exception:
            return None

    @property
    def disabled(self):
        """
        Check if the template is disabled.

        Returns:
            bool: True if the template is disabled, False otherwise.

        Example::

            if wrapped.disabled:
                print("Template is disabled")
        """
        try:
            if hasattr(self._concrete, "Disabled"):
                return self._concrete.Disabled
            return False
        except Exception:
            return False

    # ========== Slot Properties (access to slot collections) ==========

    @property
    def prefix_slots(self) -> "list[object]":
        """
        Get the prefix slots collection.

        Returns:
            List or collection of prefix slot objects, or empty list if none.

        Example::

            for slot in wrapped.prefix_slots:
                print(f"Prefix slot: {slot.Name}")

        Notes:
            - Access via PrefixSlotsRS from the concrete interface
            - Returns empty list if slots not available
        """
        try:
            if hasattr(self._concrete, "PrefixSlotsRS"):
                slots = self._concrete.PrefixSlotsRS
                return list(slots) if slots else []
            return []
        except Exception:
            return []

    @property
    def suffix_slots(self):
        """
        Get the suffix slots collection.

        Returns:
            List or collection of suffix slot objects, or empty list if none.

        Example::

            for slot in wrapped.suffix_slots:
                print(f"Suffix slot: {slot.Name}")

        Notes:
            - Access via SuffixSlotsRS from the concrete interface
            - Returns empty list if slots not available
        """
        try:
            if hasattr(self._concrete, "SuffixSlotsRS"):
                slots = self._concrete.SuffixSlotsRS
                return list(slots) if slots else []
            return []
        except Exception:
            return []

    @property
    def proclitic_slots(self):
        """
        Get the proclitic slots collection.

        Returns:
            List or collection of proclitic slot objects, or empty list if none.

        Example::

            for slot in wrapped.proclitic_slots:
                print(f"Proclitic slot: {slot.Name}")

        Notes:
            - Access via ProcliticSlotsRS from the concrete interface
            - Returns empty list if slots not available
        """
        try:
            if hasattr(self._concrete, "ProcliticSlotsRS"):
                slots = self._concrete.ProcliticSlotsRS
                return list(slots) if slots else []
            return []
        except Exception:
            return []

    @property
    def enclitic_slots(self):
        """
        Get the enclitic slots collection.

        Returns:
            List or collection of enclitic slot objects, or empty list if none.

        Example::

            for slot in wrapped.enclitic_slots:
                print(f"Enclitic slot: {slot.Name}")

        Notes:
            - Access via EncliticSlotsRS from the concrete interface
            - Returns empty list if slots not available
        """
        try:
            if hasattr(self._concrete, "EncliticSlotsRS"):
                slots = self._concrete.EncliticSlotsRS
                return list(slots) if slots else []
            return []
        except Exception:
            return []

    # ========== Convenience Properties (counts and totals) ==========

    @property
    def prefix_slot_count(self):
        """
        Get the number of prefix slots.

        Returns:
            int: Number of prefix slots (0 if none).

        Example::

            print(f"Prefix slots: {wrapped.prefix_slot_count}")
        """
        try:
            return len(self.prefix_slots)
        except Exception:
            return 0

    @property
    def suffix_slot_count(self):
        """
        Get the number of suffix slots.

        Returns:
            int: Number of suffix slots (0 if none).

        Example::

            print(f"Suffix slots: {wrapped.suffix_slot_count}")
        """
        try:
            return len(self.suffix_slots)
        except Exception:
            return 0

    @property
    def proclitic_slot_count(self):
        """
        Get the number of proclitic slots.

        Returns:
            int: Number of proclitic slots (0 if none).

        Example::

            print(f"Proclitic slots: {wrapped.proclitic_slot_count}")
        """
        try:
            return len(self.proclitic_slots)
        except Exception:
            return 0

    @property
    def enclitic_slot_count(self):
        """
        Get the number of enclitic slots.

        Returns:
            int: Number of enclitic slots (0 if none).

        Example::

            print(f"Enclitic slots: {wrapped.enclitic_slot_count}")
        """
        try:
            return len(self.enclitic_slots)
        except Exception:
            return 0

    @property
    def total_slots(self):
        """
        Get the total number of slots across all types.

        Returns the sum of prefix, suffix, proclitic, and enclitic slots.

        Returns:
            int: Total slot count (0 if no slots).

        Example::

            print(f"Total slots: {wrapped.total_slots}")
        """
        try:
            return (
                self.prefix_slot_count + self.suffix_slot_count + self.proclitic_slot_count + self.enclitic_slot_count
            )
        except Exception:
            return 0

    @property
    def owner_pos(self):
        """
        Get the owner Part of Speech for this template.

        Convenience property to access the POS that owns this template.

        Returns:
            IPartOfSpeech or None: The owner POS, or None if not available.

        Example::

            if wrapped.owner_pos:
                print(f"Template for POS: {wrapped.owner_pos.Name}")
        """
        # OwnerOfClass is an LCM method requiring an Int32 class ID argument.
        # The previous code read it as a bare attribute (returning the bound
        # method object) and the hasattr guard was always True (every ICmObject
        # has OwnerOfClass), so the caller always received a method object
        # instead of an IPartOfSpeech.  (Pattern G, issue #152)
        if not hasattr(self._concrete, "OwnerOfClass"):
            return None
        pos_lcm = self._concrete.OwnerOfClass(PartOfSpeechTags.kClassId)
        if pos_lcm is None:
            return None
        return IPartOfSpeech(pos_lcm) if IPartOfSpeech is not None else pos_lcm

    # ========== Capability Checks (for slot-specific operations) ==========

    @property
    def has_prefix_slots(self):
        """
        Check if this template has prefix slots.

        Returns:
            bool: True if template has at least one prefix slot.

        Example::

            if wrapped.has_prefix_slots:
                print(f"Template has {wrapped.prefix_slot_count} prefix slots")
        """
        return self.prefix_slot_count > 0

    @property
    def has_suffix_slots(self):
        """
        Check if this template has suffix slots.

        Returns:
            bool: True if template has at least one suffix slot.

        Example::

            if wrapped.has_suffix_slots:
                print(f"Template has {wrapped.suffix_slot_count} suffix slots")
        """
        return self.suffix_slot_count > 0

    @property
    def has_proclitic_slots(self):
        """
        Check if this template has proclitic slots.

        Returns:
            bool: True if template has at least one proclitic slot.

        Example::

            if wrapped.has_proclitic_slots:
                print(f"Template has {wrapped.proclitic_slot_count} proclitic slots")
        """
        return self.proclitic_slot_count > 0

    @property
    def has_enclitic_slots(self):
        """
        Check if this template has enclitic slots.

        Returns:
            bool: True if template has at least one enclitic slot.

        Example::

            if wrapped.has_enclitic_slots:
                print(f"Template has {wrapped.enclitic_slot_count} enclitic slots")
        """
        return self.enclitic_slot_count > 0

    @property
    def has_any_slots(self):
        """
        Check if this template has any slots at all.

        Returns:
            bool: True if template has at least one slot of any type.

        Example::

            if wrapped.has_any_slots:
                print(f"Template has {wrapped.total_slots} total slots")
        """
        return self.total_slots > 0

    # ========== Advanced: Direct C# class access (optional for power users) ==========

    @property
    def concrete(self):
        """
        Get the raw concrete interface object.

        For advanced users who need to access the underlying C# interface
        directly without going through wrapper properties.

        Returns:
            The concrete interface object (IMoInflAffixTemplate).

        Example::

            # Direct access to concrete interface
            concrete = template_obj.concrete
            prefix_slots = concrete.PrefixSlotsRS

        Notes:
            - For power users only
            - Bypasses the wrapper's abstraction
            - Normal users should prefer wrapper properties like
              has_prefix_slots, prefix_slot_count, etc.
        """
        return self._concrete

    def __repr__(self):
        """String representation showing template name."""
        return f"AffixTemplate({self.name or 'Unnamed'})"

    def __str__(self):
        """Human-readable description."""
        if self.name:
            return f"Template '{self.name}' ({self.total_slots} slots)"
        return f"Unnamed template ({self.total_slots} slots)"
