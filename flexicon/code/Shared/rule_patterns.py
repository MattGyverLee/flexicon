#
#   rule_patterns.py
#
#   Module: Pattern-element types for the
#           PhonologicalRuleOperations.WireRule composer.
#
#           These are inert dataclasses used to describe rule contexts
#           at the wrapper level. The composer translates them into
#           LCM simple-context objects.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Pattern-element types for the PhonologicalRuleOperations.WireRule composer.

These are inert dataclasses used to describe rule contexts at the wrapper
level. The composer translates them into LCM simple-context objects.

Usage::

    from flexlibs2 import Seg, NC, Boundary

    # Build context elements
    seg_t = Seg(phoneme_t)
    vowels_back = NC(vowel_class, plus=[alpha_back])
    word_bdry = Boundary("#")

Greek-variable identity is preserved by re-using the SAME
IPhFeatureConstraint object across multiple NC pattern elements.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Seg:
    """A single-phoneme pattern element.

    Args:
        phoneme: An IPhPhoneme, HVO (int), or wrapper representing a
            single phoneme.

    Notes:
        Seg carries no alpha-feature constraints: LCM's
        ``IPhSimpleContextSeg`` has no ``PlusConstrRS`` / ``MinusConstrRS``
        slots -- only ``IPhSimpleContextNC`` does. To express alpha-feature
        constraints on a single phoneme, wrap it in a singleton
        ``IPhNaturalClass`` and use ``NC(class, plus=[...], minus=[...])``
        instead. A singleton NC can be reused across rules that target
        the same phoneme. (Linguistic context: e.g. Bantu N-place
        assimilation -- see issue #23.)
    """
    phoneme: object


@dataclass(frozen=True)
class NC:
    """A natural-class pattern element, optionally with alpha-feature constraints.

    Args:
        natural_class: An IPhNaturalClass, HVO (int), or wrapper.
        plus: Sequence of IPhFeatureConstraint objects to attach to
            ``PlusConstrRS`` (positive alpha-variable bindings, e.g. [+aBack]).
        minus: Sequence of IPhFeatureConstraint objects to attach to
            ``MinusConstrRS`` (negative alpha-variable bindings, e.g. [-aBack]).

    Notes:
        Re-use the SAME IPhFeatureConstraint object across multiple
        positions to express alpha/beta/gamma agreement.
    """
    natural_class: object
    plus: tuple = ()
    minus: tuple = ()


@dataclass(frozen=True)
class Boundary:
    """A boundary marker pattern element, identified by its FW-shipped name.

    Args:
        marker: One of FieldWorks' standard boundary marker names. The
            default project ships with ``"#"`` (word boundary), ``"+"``
            (morpheme boundary), and ``"."`` (syllable boundary).

    Notes:
        Boundary elements appear only in left/right contexts (never in
        the structural change). The composer looks the marker up by
        name from ``PhonemeSetsOS[0].BoundaryMarkersOC`` rather than
        creating new markers.
    """
    marker: str = "#"


__all__ = ["Seg", "NC", "Boundary"]
