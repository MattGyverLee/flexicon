#
#   affix_slot.py
#
#   Class: AffixSlot
#          Wrapper for inflectional affix slot objects providing unified
#          interface access to slot properties and the affixes that fill
#          them.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

"""
Wrapper class for affix slot objects with unified interface.

This module provides AffixSlot, a wrapper class that transparently handles
inflectional affix slot objects (MoInflAffixSlot), providing convenient
access to a slot's name, whether it is optional, and the affixes that fill
it.

Problem:
    ``IMoInflAffixSlot.Name`` is an ``IMultiUnicode``, not a string, so
    printing it directly (``print(slot.Name)``) does not produce readable
    text -- issue #542. Callers had no public way to read a slot's name,
    optionality, or the affixes filling it without dropping to raw LCM
    access.

Solution:
    AffixSlot wrapper provides:
    - ``.name`` -- the slot name as a plain string (analysis WS, ``***``
      normalized to empty)
    - ``.optional`` -- bool
    - ``.affixes`` -- the ``IMoInflAffMsa`` objects whose ``SlotsRC``
      contains this slot, read via the direct ``IMoInflAffixSlot.Affixes``
      back-reference
    - ``.owner_pos`` -- the owning ``IPartOfSpeech``, if any

Example::

    from flexicon.code.Grammar.affix_slot import AffixSlot

    slot = posOps.GetAffixSlots(verb)[0]  # already an AffixSlot
    print(slot.name)
    print(slot.optional)
    for affix_msa in slot.affixes:
        print(affix_msa.Hvo)
"""

from ..Shared.wrapper_base import LCMObjectWrapper

try:
    from SIL.LCModel import IPartOfSpeech, PartOfSpeechTags
except ImportError:
    # Mock for testing without FieldWorks installed
    IPartOfSpeech = None

    class PartOfSpeechTags:
        kClassId = 0


class AffixSlot(LCMObjectWrapper):
    """
    Wrapper for inflectional affix slot objects providing unified
    interface access.

    Handles MoInflAffixSlot objects transparently, providing common
    properties without exposing ClassName or casting.

    Attributes:
        _obj: The base interface object (IMoInflAffixSlot)
        _concrete: The concrete type object (IMoInflAffixSlot)

    Example::

        slot = posOps.GetAffixSlots(verb)[0]
        print(slot.name)
        if slot.optional:
            print("Slot may be left empty")
    """

    def __init__(self, lcm_slot):
        """
        Initialize AffixSlot wrapper with a slot object.

        Args:
            lcm_slot: An IMoInflAffixSlot object. Typically from
                ``POSOperations.GetAffixSlots()`` or
                ``AffixTemplate.prefix_slots`` / ``.suffix_slots`` /
                ``.proclitic_slots`` / ``.enclitic_slots``.

        Example::

            slot = posOps.GetAffixSlots(verb)[0]
            wrapped = AffixSlot(slot)
        """
        super().__init__(lcm_slot)

    @property
    def name(self) -> str:
        """
        Get the slot's name.

        Returns:
            str: The slot name in the analysis writing system, or empty
            string if not set (including FLEx's ``***`` null marker).

        Example::

            print(f"Slot: {slot.name}")
        """
        from ..Shared.string_utils import normalize_text
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        name_multistring = self._obj.Name
        if not name_multistring:
            return ""
        default_ws = self._obj.Cache.DefaultAnalWs
        name_text = ITsString(name_multistring.get_String(default_ws)).Text
        return normalize_text(name_text)

    @property
    def optional(self) -> bool:
        """
        Check whether the slot may be left empty.

        Returns:
            bool: True if the slot is optional, False if it is obligatory
            (FLEx's default for a newly-created slot).

        Example::

            if slot.optional:
                print("This slot may be left empty")
        """
        try:
            return bool(self._concrete.Optional)
        except Exception:
            return False

    @property
    def affixes(self) -> "list[object]":
        """
        Get the inflectional-affix MSAs that fill this slot.

        Returns:
            list: ``IMoInflAffMsa`` objects whose ``SlotsRC`` contains this
            slot, read via the direct ``IMoInflAffixSlot.Affixes``
            back-reference. Empty list if none.

        Example::

            for affix_msa in slot.affixes:
                print(affix_msa.Hvo)

        Notes:
            - Access via the ``Affixes`` back-reference property on the
              concrete interface (confirmed by live reflection: returns
              ``IEnumerable<IMoInflAffMsa>``); this is the single most
              direct LCM path, since it is already the inverse of
              ``IMoInflAffMsa.SlotsRC``.
        """
        try:
            if hasattr(self._concrete, "Affixes"):
                affixes = self._concrete.Affixes
                return list(affixes) if affixes else []
            return []
        except Exception:
            return []

    @property
    def owner_pos(self):
        """
        Get the owner Part of Speech for this slot.

        Returns:
            IPartOfSpeech or None: The owner POS, or None if not available.

        Example::

            if slot.owner_pos:
                print(f"Slot for POS: {slot.owner_pos.Name}")
        """
        if not hasattr(self._concrete, "OwnerOfClass"):
            return None
        pos_lcm = self._concrete.OwnerOfClass(PartOfSpeechTags.kClassId)
        if pos_lcm is None:
            return None
        return IPartOfSpeech(pos_lcm) if IPartOfSpeech is not None else pos_lcm

    def __repr__(self):
        """String representation showing slot name."""
        return f"AffixSlot({self.name or 'Unnamed'})"

    def __str__(self):
        """Human-readable description."""
        suffix = " (optional)" if self.optional else ""
        if self.name:
            return f"Slot '{self.name}'{suffix}"
        return f"Unnamed slot{suffix}"
