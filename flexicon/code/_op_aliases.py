#
#   _op_aliases.py
#
#   Operation-namespace naming aliases for FLExProject (issue #200).
#
#   FLExProject exposes one accessor per operation namespace. The canonical
#   convention is PLURAL for collection namespaces (project.MorphRules,
#   project.InflectionFeatures, project.Senses, ...). Users -- and AI
#   assistants -- routinely guess the singular form and hit an AttributeError,
#   costing a full preflight + execute round trip (see the FlexToolsMCP runtime
#   logs cited in issue #200).
#
#   To make wrong-number guesses recoverable, every canonical accessor gets a
#   deprecated alias for the other grammatical number. The alias resolves to
#   the canonical accessor and emits a DeprecationWarning naming it, so scripts
#   keep working while their authors are steered to the canonical spelling.
#
#   This module is deliberately free of any SIL / pythonnet imports so the
#   alias table and generator can be unit-tested without FieldWorks installed
#   (see tests/test_flexproject_aliases.py).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
"""Deprecated singular/plural aliases for FLExProject operation accessors."""

import warnings


# Mapping is alias_name -> canonical_name. Add new operation namespaces here
# (both directions where a reasonable person might guess either) rather than
# hand-writing alias properties on FLExProject.
OP_NAMESPACE_ALIASES = {
    # --- singular guess -> canonical plural accessor ---
    "Wordform": "Wordforms",
    "WfiAnalysis": "WfiAnalyses",
    "Paragraph": "Paragraphs",
    "Segment": "Segments",
    "Phoneme": "Phonemes",
    "NaturalClass": "NaturalClasses",
    "Environment": "Environments",
    "Allomorph": "Allomorphs",
    "MorphRule": "MorphRules",                  # issue #200 (logged)
    "InflectionFeature": "InflectionFeatures",  # issue #200 (logged)
    "PhonRule": "PhonRules",
    "PhonFeature": "PhonFeatures",
    "Stratum": "Strata",
    "Sense": "Senses",
    "Example": "Examples",
    "LexReference": "LexReferences",
    "ReversalIndex": "ReversalIndexes",
    "ReversalEntry": "ReversalEntries",
    "SemanticDomain": "SemanticDomains",
    "Pronunciation": "Pronunciations",
    "Variant": "Variants",
    "PossibilityList": "PossibilityLists",
    "LocalizedList": "LocalizedLists",
    "CustomField": "CustomFields",
    "WritingSystem": "WritingSystems",
    "WfiGloss": "WfiGlosses",
    "WfiMorphBundle": "WfiMorphBundles",
    "Text": "Texts",
    "Note": "Notes",
    "Filter": "Filters",
    "Publication": "Publications",
    "Agent": "Agents",
    "Overlay": "Overlays",
    "TranslationType": "TranslationTypes",
    "AnnotationDef": "AnnotationDefs",
    "Check": "Checks",
    "ConstChart": "ConstCharts",
    "ConstChartRow": "ConstChartRows",
    "ConstChartWordGroup": "ConstChartWordGroups",
    "ConstChartMarker": "ConstChartMarkers",
    "ConstChartCellTag": "ConstChartCellTags",
    "ConstChartClauseMarker": "ConstChartClauseMarkers",
    # --- plural guess -> canonical singular accessor ---
    "LexEntries": "LexEntry",
    "MSAs": "MSA",
    "Etymologies": "Etymology",
    "GramCats": "GramCat",
}


def make_op_namespace_alias(alias_name, canonical_name):
    """Build a deprecated alias property forwarding to a canonical accessor.

    The generated property resolves to ``obj.<canonical_name>`` and warns
    (DeprecationWarning) so callers are steered to the canonical spelling
    without their code breaking.

    Args:
        alias_name: The deprecated (mis-numbered) accessor name.
        canonical_name: The canonical accessor to forward to.

    Returns:
        property: A read-only property suitable for ``setattr`` onto a class.
    """

    def _getter(self, _canonical=canonical_name, _alias=alias_name):
        warnings.warn(
            "FLExProject.{alias} is a deprecated alias; use "
            "project.{canonical} instead.".format(
                alias=_alias, canonical=_canonical
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, _canonical)

    _getter.__name__ = alias_name
    _getter.__doc__ = (
        "Deprecated alias for :attr:`{canonical}`. Emits a "
        "DeprecationWarning and forwards to the canonical accessor "
        "(issue #200).".format(canonical=canonical_name)
    )
    return property(_getter)


def install_op_namespace_aliases(cls, aliases=None):
    """Attach the generated alias properties to a class (FLExProject).

    Only names that are not already real attributes of the class are added,
    so a canonical accessor can never be shadowed by a generated alias. Any
    alias whose canonical target is missing is a programming error in the
    table and raises at import time.

    Args:
        cls: The class to receive the alias properties.
        aliases: Optional alias_name -> canonical_name mapping. Defaults to
            OP_NAMESPACE_ALIASES.

    Returns:
        list[str]: The alias names that were installed (skipping any that
        collided with a real accessor).
    """
    if aliases is None:
        aliases = OP_NAMESPACE_ALIASES

    installed = []
    for alias_name, canonical_name in aliases.items():
        if not hasattr(cls, canonical_name):
            raise AttributeError(
                "OP_NAMESPACE_ALIASES maps {alias!r} to unknown canonical "
                "accessor {canonical!r} on {cls}".format(
                    alias=alias_name, canonical=canonical_name, cls=cls.__name__
                )
            )
        if hasattr(cls, alias_name):
            # Never clobber a real accessor with a generated alias.
            continue
        setattr(cls, alias_name, make_op_namespace_alias(alias_name, canonical_name))
        installed.append(alias_name)
    return installed
