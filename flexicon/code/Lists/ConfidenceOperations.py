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

# Import FLEx LCM types
from SIL.LCModel import (
    IWfiAnalysisRepository,
    IWfiGlossRepository,
)

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

    Confidence levels are used to rate the quality or certainty of linguistic
    analyses and glosses. They provide a standardized way to indicate how
    confident a linguist or parser is about a particular analysis or gloss.
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
    - GetAnalysesWithConfidence() - Find analyses using a level
    - GetGlossesWithConfidence() - Find glosses using a level
    - GetDefault() - Get default confidence level

    This class should be accessed via FLExProject.Confidence property.

    Usage::

        from flexlibs2 import FLExProject

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
            # Get analyses using this confidence level
            analyses = project.Confidence.GetAnalysesWithConfidence(high)
            print(f"{len(analyses)} analyses have high confidence")

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
        Get all wordform analyses that use this confidence level.

        Args:
            level_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            list: List of IWfiAnalysis objects that reference this confidence level.

        Raises:
            FP_NullParameterError: If level_or_hvo is None.

        Example:
            >>> high = project.Confidence.Find("High Confidence")
            >>> analyses = project.Confidence.GetAnalysesWithConfidence(high)
            >>> print(f"Found {len(analyses)} high-confidence analyses")
            Found 127 high-confidence analyses

            >>> # Show analyses for each confidence level
            >>> for level in project.Confidence.GetAll():
            ...     name = project.Confidence.GetName(level)
            ...     analyses = project.Confidence.GetAnalysesWithConfidence(level)
            ...     print(f"{name}: {len(analyses)} analyses")

            >>> # Find analyses that need review
            >>> low = project.Confidence.Find("Low Confidence")
            >>> if low:
            ...     review_list = project.Confidence.GetAnalysesWithConfidence(low)
            ...     for analysis in review_list:
            ...         # Process analyses needing review
            ...         pass

        Notes:
            - Searches through all wordform analyses in the project
            - Returns empty list if no analyses use this confidence level
            - May be slow for large lexicons (searches entire repository)
            - Useful for quality control and validation workflows
            - Use before deleting a confidence level

        See Also:
            GetGlossesWithConfidence, Delete
        """
        self._ValidateParam(level_or_hvo, "level_or_hvo")

        level = self._PossibilityItemOperations__ResolveObject(level_or_hvo)
        level_hvo = level.Hvo

        analyses = []
        analysis_repo = self.project.project.ServiceLocator.GetInstance(IWfiAnalysisRepository)

        # Search through all analyses
        for analysis in analysis_repo.AllInstances():
            # Check if this analysis has this confidence level
            # Note: IWfiAnalysis may have Confidence property as reference
            if hasattr(analysis, "ConfidenceRA") and analysis.ConfidenceRA:
                if analysis.ConfidenceRA.Hvo == level_hvo:
                    analyses.append(analysis)

        return analyses

    @OperationsMethod
    def GetGlossesWithConfidence(self, level_or_hvo):
        """
        Get all wordform glosses that use this confidence level.

        Args:
            level_or_hvo: Either an ICmPossibility object or its HVO.

        Returns:
            list: List of IWfiGloss objects that reference this confidence level.

        Raises:
            FP_NullParameterError: If level_or_hvo is None.

        Example:
            >>> high = project.Confidence.Find("High Confidence")
            >>> glosses = project.Confidence.GetGlossesWithConfidence(high)
            >>> print(f"Found {len(glosses)} high-confidence glosses")
            Found 89 high-confidence glosses

            >>> # Show glosses for each confidence level
            >>> for level in project.Confidence.GetAll():
            ...     name = project.Confidence.GetName(level)
            ...     glosses = project.Confidence.GetGlossesWithConfidence(level)
            ...     print(f"{name}: {len(glosses)} glosses")

            >>> # Find glosses that need verification
            >>> unconfirmed = project.Confidence.Find("Unconfirmed")
            >>> if unconfirmed:
            ...     pending = project.Confidence.GetGlossesWithConfidence(unconfirmed)
            ...     for gloss in pending:
            ...         # Process glosses needing verification
            ...         pass

        Notes:
            - Searches through all wordform glosses in the project
            - Returns empty list if no glosses use this confidence level
            - May be slow for large projects (searches entire repository)
            - Useful for tracking translation quality
            - Use before deleting a confidence level

        See Also:
            GetAnalysesWithConfidence, Delete
        """
        self._ValidateParam(level_or_hvo, "level_or_hvo")

        level = self._PossibilityItemOperations__ResolveObject(level_or_hvo)
        level_hvo = level.Hvo

        glosses = []
        gloss_repo = self.project.project.ServiceLocator.GetInstance(IWfiGlossRepository)

        # Search through all glosses
        for gloss in gloss_repo.AllInstances():
            # Check if this gloss has this confidence level
            # Note: IWfiGloss may have Confidence property as reference
            if hasattr(gloss, "ConfidenceRA") and gloss.ConfidenceRA:
                if gloss.ConfidenceRA.Hvo == level_hvo:
                    glosses.append(gloss)

        return glosses

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
