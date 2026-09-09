#
#   GramCatOperations.py
#
#   Class: GramCatOperations
#          DEPRECATED alias of POSOperations, retained only so that the
#          symbol stays importable. Grammatical Category operations for
#          FieldWorks Language Explorer projects via SIL Language and
#          Culture Model (LCM) API now live on POSOperations.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""Deprecated alias of :class:`POSOperations` (issue #276).

The former implementation walked ``LangProject.MsFeatureSystemOA.TypesOC``,
a collection of ``IFsFeatStrucType``. That was the wrong collection: an
``IFsFeatStrucType`` is a structural template for feature structures and is
never a grammatical category. Because those elements are not
``ICmPossibility`` and have no ``SubPossibilitiesOS``, ``recursive=True``
silently truncated, ``Create(parent=)`` and ``GetSubcategories`` could not
work, and ``Delete`` removed from the wrong collection.

At list level a grammatical category *is* a Part of Speech
(``IPartOfSpeech`` in ``LangProject.PartsOfSpeechOA``), a list
``POSOperations`` already owns completely. So this class is now a thin
deprecated subclass of it rather than a second CRUD surface.
"""

import warnings

# Import the canonical implementation this class now delegates to
from .POSOperations import POSOperations

# Import BaseOperations decorators
from ..BaseOperations import OperationsMethod

# Import flexicon exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class GramCatOperations(POSOperations):
    """
    Deprecated alias of :class:`POSOperations` -- use ``project.POS``.

    Instantiating this class emits a :class:`DeprecationWarning`. Every
    operation is inherited from ``POSOperations`` and addresses
    ``LangProject.PartsOfSpeechOA``; the only override is :meth:`Create`,
    which raises rather than repeating a write that was never correct.

    **The ruling (issue #276).** Three FLEx concepts wear confusingly
    similar names. They are different LCM classes, and only the first is a
    category:

    - ``project.POS`` (formerly ``project.GramCat``) -- the **category
      inventory** (FLEx: Grammar > Categories). Create, browse, nest and
      delete categories here. A list-level "grammatical category" is a
      Part of Speech.
    - ``project.Senses.GetGrammaticalInfo(sense)`` -- the sense-level
      composite, the **MSA** (``ILexSense.MorphoSyntaxAnalysisRA``), which
      is what FLEx labels "Grammatical Info." Use
      ``project.Senses.GetPartOfSpeechObject(sense)`` for just the category
      behind it, and ``project.MSA.*`` to build one.
    - ``project.InflectionFeatures`` -- the feature side of that composite,
      including the ``MsFeatureSystemOA.TypesOC`` entries this class used
      to walk, via ``TypeFind`` / ``TypeCreate``. An ``IFsFeatStrucType``
      is never a grammatical category.

    Removal is scheduled for the v5.0.0 boundary, alongside the other
    deprecated compatibility surfaces.

    Usage::

        from flexicon import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Preferred spelling. project.GramCat addresses this same list
        # (LangProject.PartsOfSpeechOA) but is a distinct deprecated
        # object: project.GramCat is project.POS is False, and its
        # Create() always raises. See FLExProject.GramCat.
        posOps = project.POS

        for pos in posOps.GetAll():
            print(posOps.GetName(pos), posOps.GetAbbreviation(pos))

        verb = posOps.Create("Verb", "v")
        transitive = posOps.AddSubcategory(verb, "Transitive Verb", "vt")
        assert posOps.GetParent(transitive) is not None

        project.CloseProject()

    See Also:
        POSOperations, InflectionFeatureOperations.TypeCreate,
        LexSenseOperations.GetGrammaticalInfo
    """

    def __init__(self, project):
        """
        Initialize the deprecated alias and warn.

        Args:
            project: The FLExProject instance to operate on.

        Warns:
            DeprecationWarning: Always. Names ``project.POS`` /
                ``POSOperations`` as the replacement.
        """
        warnings.warn(
            "GramCatOperations is a deprecated alias for POSOperations; use "
            "project.POS (or POSOperations directly) instead. A list-level "
            "grammatical category is a Part of Speech; the feature-structure "
            "types this class used to walk live at "
            "project.InflectionFeatures (issue #276).",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(project)

    @OperationsMethod
    def Create(self, name, parent=None):
        """
        Removed -- always raises. Use ``project.POS.Create`` instead.

        The old signature is retained so that an existing caller gets an
        explanatory :class:`FP_ParameterError` rather than a bare
        ``TypeError`` about a missing ``abbreviation`` argument.

        Args:
            name: Accepted and ignored -- the former category name.
            parent: Accepted and ignored -- the former parent category.

        Raises:
            FP_ParameterError: Always, before any write. Nothing is
                created and no transaction is opened.

        Notes:
            There is no correct behaviour here to preserve. Every
            ``GramCat.Create`` call ever made added a stray
            ``IFsFeatStrucType`` to ``MsFeatureSystemOA.TypesOC`` -- an
            entry that shows up in FLEx under Grammar > Features, not
            under Grammar > Categories (issue #276). Projects that called
            it have strays to hand-clean; no automatic cleanup is offered
            because a stray is indistinguishable from legitimate
            ``TypeCreate`` output.

        See Also:
            POSOperations.Create, POSOperations.AddSubcategory,
            InflectionFeatureOperations.TypeCreate
        """
        raise FP_ParameterError(
            "GramCat.Create() has been removed (issue #276): it never "
            "created a grammatical category. It created a stray "
            "IFsFeatStrucType in the feature system "
            "(LangProject.MsFeatureSystemOA.TypesOC), which is a structural "
            "template for feature structures, not a category. A list-level "
            "grammatical category is a Part of Speech: use "
            "project.POS.Create(name, abbreviation) for a top-level "
            "category, or "
            "project.POS.AddSubcategory(parent, name, abbreviation) for a "
            "subcategory. If you did want a feature-structure type, use "
            "project.InflectionFeatures.TypeCreate(name, abbreviation)."
        )
