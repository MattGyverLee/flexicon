#
#   morph_type_utils.py
#
#   Module: Shared morph-type resolution utilities.
#           Used by LexEntryOperations and AllomorphOperations (and any
#           other operations class that needs to turn a user-supplied
#           morph-type name into an IMoMorphType object) so that the
#           lookup, display-marker normalization, and stem/affix
#           classification logic live in exactly one place.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from SIL.LCModel import MoMorphTypeTags

from .string_utils import best_analysis_text, normalize_match_key

# Canonical morph-type names recognized by FLEx's standard MoMorphType
# possibility list. This is the union of every kguidMorph* GUID already
# referenced elsewhere in this codebase:
#   - the "stem role" set (_STEM_MORPH_TYPE_GUIDS / is_stem_morph_type):
#     stem, root, bound root, bound stem, clitic, enclitic, proclitic,
#     particle, phrase, discontiguous phrase
#   - the "affix role" set (everything is_stem_morph_type reports False
#     for, per LexSenseOperations.__EntryHasAffixMorphType): prefix,
#     suffix, infix, circumfix, prefixing/suffixing/infixing interfix,
#     simulfix, suprafix
# It is enumerated from existing code, not guessed, and is used only to
# build a complete, honest error message -- actual resolution always
# queries the live MorphTypesOA possibility list (see find_morph_type).
CANONICAL_MORPH_TYPE_NAMES = (
    "bound root",
    "bound stem",
    "circumfix",
    "clitic",
    "discontiguous phrase",
    "enclitic",
    "infix",
    "infixing interfix",
    "particle",
    "phrase",
    "prefix",
    "prefixing interfix",
    "proclitic",
    "root",
    "simulfix",
    "stem",
    "suffix",
    "suffixing interfix",
    "suprafix",
)

# GUIDs whose allomorphs use MoStemAllomorph (as opposed to
# MoAffixAllomorph). Matches FLEx logic in MorphTypeAtomicLauncher.cs.
_STEM_MORPH_TYPE_GUIDS = frozenset(
    {
        MoMorphTypeTags.kguidMorphStem,
        MoMorphTypeTags.kguidMorphRoot,
        MoMorphTypeTags.kguidMorphBoundRoot,
        MoMorphTypeTags.kguidMorphBoundStem,
        MoMorphTypeTags.kguidMorphClitic,
        MoMorphTypeTags.kguidMorphEnclitic,
        MoMorphTypeTags.kguidMorphProclitic,
        MoMorphTypeTags.kguidMorphParticle,
        MoMorphTypeTags.kguidMorphPhrase,
        MoMorphTypeTags.kguidMorphDiscontiguousPhrase,
    }
)


def strip_display_marker(name):
    """
    Strip FLEx's decorated display markers so a UI-copied label resolves
    to the same canonical name as the bare form.

    FLEx shows morph-type-decorated forms in several UI surfaces, e.g.
    '=enclitic', 'proclitic=', '-suffix', '~simulfix~', '<infix>'. None of
    these markers are part of the canonical IMoMorphType.Name; they are
    stripped (leading and trailing) before matching.

    Args:
        name (str): Raw name, with or without display markers.

    Returns:
        str: The bare name with leading/trailing '-', '=', '~', '<', '>'
             removed.
    """
    return name.strip("-=~<>")


def find_morph_type(project, name):
    """
    Find an IMoMorphType by name (case-insensitive), tolerating FLEx's
    decorated display labels.

    Args:
        project: The FLExProject instance (must expose ``project.lp``).
        name (str): The morph type name to search for, bare or decorated
            (e.g. 'suffix', '=enclitic', 'proclitic=', '-suffix').

    Returns:
        IMoMorphType or None: The resolved morph type, or None if no
        possibility (including sub-possibilities) matches.
    """
    bare = strip_display_marker(name)
    target = normalize_match_key(bare, casefold=True)

    morph_types = project.lp.LexDbOA.MorphTypesOA
    if morph_types is None:
        return None

    def _search(possibilities):
        for mt in possibilities:
            mt_name = best_analysis_text(mt.Name)
            if mt_name and normalize_match_key(mt_name, casefold=True) == target:
                return mt
            if mt.SubPossibilitiesOS.Count > 0:
                found = _search(mt.SubPossibilitiesOS)
                if found:
                    return found
        return None

    return _search(morph_types.PossibilitiesOS)


def is_stem_morph_type(morph_type):
    """
    Determine if a morph type should use MoStemAllomorph or MoAffixAllomorph.

    Args:
        morph_type: IMoMorphType object, or None.

    Returns:
        bool: True if stem type (uses MoStemAllomorph), False if affix type.
            Defaults to True (stem) when morph_type is None.

    Raises:
        AttributeError: If ``morph_type`` is not None and does not expose a
            ``.Guid`` attribute (e.g. a bare string or other non-LCM object).

    Known limitation:
        Classification is membership in a fixed GUID set, not a live
        hierarchy check. User-defined custom stem sub-possibilities (created
        under a stem-like parent in a customized MorphTypesOA list) are not
        in ``_STEM_MORPH_TYPE_GUIDS`` and will be classified as affix.
    """
    if morph_type is None:
        return True

    return morph_type.Guid in _STEM_MORPH_TYPE_GUIDS


def morph_type_not_found_error(name):
    """
    Build the standard "morph type not found" error message, listing the
    complete set of canonical morph-type names (no vague "etc.").

    Args:
        name (str): The name the caller attempted to resolve.

    Returns:
        str: A message suitable for raising as FP_ParameterError.

    Note:
        CANONICAL_MORPH_TYPE_NAMES is a permanent static, display-only
        list enumerated from existing code (not a live MorphTypesOA
        lookup). It is intentionally not queried dynamically here --
        actual name resolution always goes through find_morph_type(),
        which does query the live possibility list.
    """
    return (
        f"Morph type '{name}' not found. "
        f"Use one of: {', '.join(CANONICAL_MORPH_TYPE_NAMES)}."
    )
