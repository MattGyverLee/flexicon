#
#   ConfidenceOperations.py
#
#   Class: ConfidenceOperations
#          Confidence level operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import OperationsMethod
from .possibility_item_base import PossibilityItemOperations


class ConfidenceOperations(PossibilityItemOperations):
    """
    This class provides operations for managing confidence levels (quality
    ratings) in a FieldWorks project.

    Confidence levels rate the quality or certainty of research notebook
    records (and other LCM types that expose ``ConfidenceRA``). They are
    not stored on interlinear ``IWfiAnalysis`` / ``IWfiGloss`` objects.
    Confidence levels are implemented as a possibility list using ICmPossibility.

    Common confidence levels might include:
    - High Confidence (for well-established analyses)
    - Medium Confidence (for probable but uncertain analyses)
    - Low Confidence (for tentative analyses)
    - Unconfirmed (for machine-generated or unverified analyses)

    Inherited CRUD Operations (from PossibilityItemOperations):
    - GetAll() - Get all confidence levels
    - Create() - Create a new confidence level
    - Delete() - Delete a confidence level
    - Duplicate() - Clone a confidence level
    - Find() - Find by name
    - Exists() - Check existence
    - GetName() / SetName() - Get/set name
    - GetDescription() / SetDescription() - Get/set description
    - GetGuid() - Get GUID
    - CompareTo() - Compare by name

    Domain-Specific Methods (ConfidenceOperations):
    - GetAnalysesWithConfidence() - Find notebook records using a level
    - GetGlossesWithConfidence() - Not supported (IWfiGloss has no confidence)
    - GetDefault() - Get default confidence level

    This class should be accessed via FLExProject.Confidence property.

    Usage::

        from flexicon import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all confidence levels
        for level in project.Confidence.GetAll():
            name = project.Confidence.GetName(level)
            desc = project.Confidence.GetDescription(level)
            print(f"{name}: {desc}")

        # Find a specific confidence level
        high = project.Confidence.Find("High Confidence")
        if high:
            # Get notebook records using this confidence level
            records = project.Confidence.GetAnalysesWithConfidence(high)
            print(f"{len(records)} records have high confidence")

        # Create a custom confidence level
        custom = project.Confidence.Create("Verified", "en")
        project.Confidence.SetDescription(custom,
            "Analysis verified by native speaker")

        # Find the default confidence level
        default = project.Confidence.GetDefault()
        if default:
            print(f"Default: {project.Confidence.GetName(default)}")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ConfidenceOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _get_item_class_name(self):
        """Get the item class name for error messages."""
        return "Confidence"

    def _get_list_object(self):
        """Get the confidence levels list container."""
        return self.project.lp.ConfidenceLevelsOA

    # --- Usage Query Operations ---

    @OperationsMethod
    def GetAnalysesWithConfidence(self, level_or_hvo):
        """
        Get all research notebook records that use this confidence level.

        Args:
            level_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            list: List of IRnGenericRec objects whose ``ConfidenceRA`` matches
            this level.

        Raises:
            FP_NullParameterError: If level_or_hvo is None.

        Example:
            >>> high = project.Confidence.Find("High Confidence")
            >>> records = project.Confidence.GetAnalysesWithConfidence(high)
            >>> print(f"Found {len(records)} high-confidence notebook records")
            Found 12 high-confidence notebook records

            >>> # Show records for each confidence level
            >>> for level in project.Confidence.GetAll():
            ...     name = project.Confidence.GetName(level)
            ...     records = project.Confidence.GetAnalysesWithConfidence(level)
            ...     print(f"{name}: {len(records)} records")

        Notes:
            - Scans ``DataNotebook.GetAll()`` (``IRnGenericRec`` with
              ``ConfidenceRA`` in LCM)
            - Interlinear ``IWfiAnalysis`` objects do not carry confidence
              levels; the historical method name is retained
            - Returns empty list if no records use this confidence level
            - Use before deleting a confidence level

        See Also:
            GetGlossesWithConfidence, Delete, DataNotebookOperations.GetConfidence
        """
        self._ValidateParam(level_or_hvo, "level_or_hvo")

        level = self._PossibilityItemOperations__ResolveObject(level_or_hvo)
        level_hvo = level.Hvo

        records = []
        for record in self.project.DataNotebook.GetAll():
            confidence = record.ConfidenceRA
            if confidence and confidence.Hvo == level_hvo:
                records.append(record)

        return records

    @OperationsMethod
    def GetGlossesWithConfidence(self, level_or_hvo):
        """
        Not supported: wordform glosses have no confidence field in LCM.

        Args:
            level_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            Never returns normally.

        Raises:
            FP_NullParameterError: If level_or_hvo is None.
            FP_ParameterError: Always -- ``IWfiGloss`` has no ``ConfidenceRA``.

        See Also:
            GetAnalysesWithConfidence, WfiAnalysisOperations
        """
        self._ValidateParam(level_or_hvo, "level_or_hvo")

        raise FP_ParameterError(
            "IWfiGloss has no confidence level in LCM; wordform glosses do "
            "not reference ConfidenceLevelsOA. Use GetAnalysesWithConfidence "
            "for notebook records, or WfiAnalysis approval APIs for "
            "interlinear quality."
        )

    # --- Special Query Operations ---

    @OperationsMethod
    def GetDefault(self):
        """
        Get the default confidence level for the project.

        The default confidence level is typically used for new analyses when
        no specific confidence level is assigned.

        Returns:
            ICmPossibility or None: The default confidence level, or None if not set.

        Example:
            >>> # Get default confidence level
            >>> default = project.Confidence.GetDefault()
            >>> if default:
            ...     name = project.Confidence.GetName(default)
            ...     print(f"Default confidence level: {name}")
            Default confidence level: Medium Confidence

            >>> # Use default for new analysis
            >>> default = project.Confidence.GetDefault()
            >>> if default:
            ...     # Apply to new analysis
            ...     pass

        Notes:
            - Returns None if no default is configured
            - Default is typically the first confidence level in the list
            - Some FLEx configurations may not have a default set
            - Default can be project-specific
            - Consider the first level or "Medium" as conventional defaults

        See Also:
            GetAll, Find
        """
        levels = self.GetAll()
        if not levels:
            return None

        # In FLEx, the first item is often the default
        # Some lists may have an IsDefault flag, but typically use first item
        return levels[0] if levels else None
