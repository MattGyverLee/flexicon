#
#   WfiAnalysisOperations.py
#
#   Class: WfiAnalysisOperations
#          Wordform analysis operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import clr

clr.AddReference("System")
import System

from SIL.LCModel import (
    IWfiAnalysis,
    IWfiAnalysisFactory,
    IWfiAnalysisRepository,
    IWfiWordform,
    IWfiGlossFactory,
    IWfiMorphBundleFactory,
    IPartOfSpeech,
    ICmAgentEvaluation,
    ICmAgent,
)

from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# --- Approval Status Enum ---

import enum


class ApprovalStatusTypes(enum.IntEnum):
    """Approval status values for wordform analyses.

    IntEnum so existing callers that compared by the underlying integer
    keep working: ``ApprovalStatusTypes.APPROVED == 2`` is still True,
    and ``int(ApprovalStatusTypes.APPROVED) == 2`` for explicit
    coercion. New callers can also pass ``True`` / ``False`` / ``None``
    directly to :meth:`SetApprovalStatus` (more user-centric per
    CLAUDE.md). (issue #59)
    """

    DISAPPROVED = 0  # Parser or human has disapproved
    UNAPPROVED = 1  # Not yet approved/reviewed
    APPROVED = 2  # Parser or human has approved


def _coerce_approval_status(status):
    """Normalize a user-facing approval value to ApprovalStatusTypes.

    Accepts:
      - ApprovalStatusTypes member -> passes through.
      - True / False / None -> APPROVED / DISAPPROVED / UNAPPROVED.
        Matches the natural mental model: "I approve this" / "I reject
        this" / "no opinion." (issue #59)
      - Bare ints 0/1/2 -> looked up against the enum members for
        back-compat with the pre-IntEnum constants.

    Raises FP_ParameterError on anything else so a typo'd value fails
    loudly instead of silently dispatching to the wrong opinion.
    """
    if isinstance(status, ApprovalStatusTypes):
        return status
    if status is True:
        return ApprovalStatusTypes.APPROVED
    if status is False:
        return ApprovalStatusTypes.DISAPPROVED
    if status is None:
        return ApprovalStatusTypes.UNAPPROVED
    if isinstance(status, int):
        try:
            return ApprovalStatusTypes(status)
        except ValueError:
            pass
    raise FP_ParameterError(
        f"status must be ApprovalStatusTypes (or True/False/None for "
        f"approved/disapproved/unapproved), got {status!r}"
    )


# --- WfiAnalysisOperations Class ---


class WfiAnalysisOperations(BaseOperations):
    """
    Provides operations for managing wordform analyses in a FLEx project.

    Wordform analyses represent linguistic analyses of wordforms, including
    morphological breakdowns, glosses, grammatical categories, and approval
    status. Each wordform can have multiple analyses representing different
    possible interpretations.

    This class should be accessed via FLExProject.WfiAnalyses property.

    Example:
        >>> project = FLExProject()
        >>> project.OpenProject("MyProject", writeEnabled=True)
        >>> # Get wordform and its analyses
        >>> wf = project.Wordforms.Find("running")
        >>> analyses = project.WfiAnalyses.GetAll(wf)
        >>> for analysis in analyses:
        ...     glosses = project.WfiAnalyses.GetGlosses(analysis)
        ...     print(f"Analysis: {glosses}")
        >>> # Create new analysis
        >>> new_analysis = project.WfiAnalyses.Create(wf)
        >>> # Add gloss
        >>> project.WfiAnalyses.AddGloss(new_analysis, "running", "en")
        >>> # Approve analysis
        >>> project.WfiAnalyses.ApproveAnalysis(new_analysis)
    """

    def __init__(self, project):
        """
        Initialize WfiAnalysisOperations.

        Args:
            project: FLExProject instance
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """Specify which sequence to reorder for wordform analyses."""
        return parent.AnalysesOS

    def __WSHandle(self, wsHandle):
        """
        Internal helper to resolve writing system handle (analysis).

        Args:
            wsHandle: Writing system handle (language tag or ID), or None for default

        Returns:
            int: Resolved writing system handle
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    def __GetWordformObject(self, wordform_or_hvo):
        """
        Internal helper to get wordform object from HVO or object.

        Args:
            wordform_or_hvo: IWfiWordform object or HVO integer.

        Returns:
            IWfiWordform: The wordform object.

        Raises:
            FP_ParameterError: If parameter doesn't refer to a wordform.
        """
        if isinstance(wordform_or_hvo, int):
            wf = self.project.Object(wordform_or_hvo)
            if not isinstance(wf, IWfiWordform):
                raise FP_ParameterError("HVO does not refer to a wordform")
            return wf
        return wordform_or_hvo

    def __GetAnalysisObject(self, analysis_or_hvo):
        """
        Internal helper to get analysis object from HVO or object.

        Args:
            analysis_or_hvo: IWfiAnalysis object or HVO integer.

        Returns:
            IWfiAnalysis: The analysis object.

        Raises:
            FP_ParameterError: If parameter doesn't refer to an analysis.
        """
        if isinstance(analysis_or_hvo, int):
            analysis = self.project.Object(analysis_or_hvo)
            if not isinstance(analysis, IWfiAnalysis):
                raise FP_ParameterError("HVO does not refer to an analysis")
            return analysis
        return analysis_or_hvo

    # --- Core CRUD Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, wordform_or_hvo):
        """
        Retrieve all analyses for a wordform.

        This method returns all IWfiAnalysis objects associated with a given
        wordform, representing different possible linguistic interpretations.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO

        Returns:
            list: List of IWfiAnalysis objects for this wordform

        Raises:
            FP_NullParameterError: If wordform_or_hvo is None
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.WfiAnalyses.GetAll(wf)
            >>> print(f"Found {len(analyses)} analyses")
            Found 2 analyses
            >>> for analysis in analyses:
            ...     if project.WfiAnalyses.IsHumanApproved(analysis):
            ...         print("This is the approved analysis")

        Notes:
            - Returns empty list if wordform has no analyses
            - Analyses may be human-created or parser-generated
            - Each analysis represents a possible linguistic interpretation
            - Analyses include morphological breakdown and glosses

        See Also:
            Create, Exists, Delete
        """
        self._ValidateParam(wordform_or_hvo, "wordform_or_hvo")

        wordform = self.__GetWordformObject(wordform_or_hvo)
        return list(wordform.AnalysesOC)

    @OperationsMethod
    def Create(self, wordform_or_hvo):
        """
        Create a new analysis for a wordform.

        Creates an empty IWfiAnalysis object associated with the specified
        wordform. After creation, use AddGloss, AddMorphBundle, SetCategory,
        etc. to populate the analysis.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO

        Returns:
            IWfiAnalysis: The newly created analysis object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If wordform_or_hvo is None
            FP_ParameterError: If wordform doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analysis = project.WfiAnalyses.Create(wf)
            >>> # Add gloss to the analysis
            >>> project.WfiAnalyses.AddGloss(analysis, "running", "en")
            >>> # Set category
            >>> verb = project.POS.Find("Verb")
            >>> if verb:
            ...     project.WfiAnalyses.SetCategory(analysis, verb)
            >>> # Approve it
            >>> project.WfiAnalyses.ApproveAnalysis(analysis)

        Notes:
            - New analyses start with unapproved status
            - Empty analyses have no glosses or morph bundles
            - Use SetApprovalStatus or ApproveAnalysis to mark as approved
            - Consider using AddGloss immediately after creation

        See Also:
            Delete, AddGloss, SetCategory, ApproveAnalysis
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(wordform_or_hvo, "wordform_or_hvo")

        wordform = self.__GetWordformObject(wordform_or_hvo)

        with self._TransactionCM("Create analysis"):
            # Create the analysis using the factory
            factory = self.project.project.ServiceLocator.GetService(IWfiAnalysisFactory)
            new_analysis = factory.Create()

            # Add to wordform's analysis collection
            wordform.AnalysesOC.Add(new_analysis)

            return new_analysis

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a wordform analysis.

        Args:
            item: The IWfiAnalysis object.

        Returns:
            dict: Dictionary of syncable properties with their values.

        Example:
            >>> props = project.WfiAnalyses.GetSyncableProperties(analysis)
            >>> print(props['CategoryRA'])
            'abc123...'  # GUID of the category (POS)

        Notes:
            - Reference Atomic property: CategoryRA (returns GUID string)
            - Does NOT include owned collections (glosses, morph bundles) - those are children
            - Does NOT include approval status (metadata)
        """
        props = {}

        # Reference Atomic property - CategoryRA (Part of Speech)
        if hasattr(item, "CategoryRA") and item.CategoryRA:
            props["CategoryRA"] = str(item.CategoryRA.Guid)

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two wordform analyses for differences.

        Args:
            item1: First analysis object (from project 1)
            item2: Second analysis object (from project 2)
            ops1: Optional WfiAnalysisOperations instance for project 1 (defaults to self)
            ops2: Optional WfiAnalysisOperations instance for project 2 (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
                - is_different (bool): True if analyses differ, False if identical
                - differences_dict (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> is_diff, diffs = ops1.CompareTo(analysis1, analysis2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} != {val2}")

        Notes:
            - Compares CategoryRA (POS) by GUID
            - Empty/null values are treated as equivalent
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}

        # Get all property keys from both items
        all_keys = set(props1.keys()) | set(props2.keys())

        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            # Compare values
            if self.project._CompareValues(val1, val2):
                # Values are different
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return (is_different, differences)

    @OperationsMethod
    def Delete(self, analysis_or_hvo):
        """
        Delete an analysis from its owning wordform.

        Removes the specified analysis from the wordform's analysis collection.
        All associated glosses and morph bundles are also deleted.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.WfiAnalyses.GetAll(wf)
            >>> # Delete disapproved analyses
            >>> for analysis in analyses:
            ...     status = project.WfiAnalyses.GetApprovalStatus(analysis)
            ...     if status == ApprovalStatusTypes.DISAPPROVED:
            ...         project.WfiAnalyses.Delete(analysis)

        Warning:
            - This is a destructive operation
            - All glosses and morph bundles are permanently deleted
            - Text segments using this analysis may be affected
            - Cannot be undone

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Get the owning wordform and remove the analysis. pythonnet
        # returns analysis.Owner as the base ICmObject, which has no
        # AnalysesOC; cast to IWfiWordform first (issue #32).
        wordform = IWfiWordform(analysis.Owner)
        wordform.AnalysesOC.Remove(analysis)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=False, deep=False):
        """
        Duplicate a wordform analysis, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IWfiAnalysis object or HVO to duplicate.
            insert_after (bool): Ignored. AnalysesOC is an unordered
                ILcmOwningCollection with no Insert() method and no concept of
                positional ordering. The duplicate is always appended via Add().
            deep (bool): If True, also duplicate owned objects (glosses, morph bundles).
                        If False (default), only copy simple properties and references.

        Returns:
            IWfiAnalysis: The newly created duplicate analysis with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.WfiAnalyses.GetAll(wf)
            >>> if analyses:
            ...     # Shallow duplicate (no glosses/morph bundles)
            ...     dup = project.WfiAnalyses.Duplicate(analyses[0])
            ...     print(f"Original: {project.WfiAnalyses.GetGuid(analyses[0])}")
            ...     print(f"Duplicate: {project.WfiAnalyses.GetGuid(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321
            ...
            ...     # Deep duplicate (includes all glosses and morph bundles)
            ...     deep_dup = project.WfiAnalyses.Duplicate(analyses[0], deep=True)
            ...     print(f"Glosses: {project.WfiAnalyses.GetGlossCount(deep_dup)}")
            ...     print(f"Morph bundles: {project.WfiAnalyses.GetMorphBundleCount(deep_dup)}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original analysis's position
            - Simple properties copied: None (analysis has no simple MultiString properties)
            - Reference properties copied: CategoryRA (part of speech)
            - Owned objects (deep=True): MeaningsOC (glosses), MorphBundlesOS (morph bundles)
            - EvaluationsRC (approval status) is NOT copied - new analysis starts unapproved

        See Also:
            Create, Delete, GetGuid
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source analysis and parent; AnalysesOC is declared on IWfiWordform
        # so cast directly instead of doing a wasteful Hvo round-trip.
        source = self.__GetAnalysisObject(item_or_hvo)
        parent = IWfiWordform(source.Owner)

        with self._TransactionCM("Duplicate analysis"):
            # Create new analysis using factory (auto-generates new GUID)
            factory = self.project.project.ServiceLocator.GetService(IWfiAnalysisFactory)
            duplicate = factory.Create()

            # AnalysesOC is an unordered ILcmOwningCollection; insert_after has
            # no semantic meaning and is ignored.
            parent.AnalysesOC.Add(duplicate)

            # Copy Reference Atomic (RA) properties
            if hasattr(source, "CategoryRA") and source.CategoryRA:
                duplicate.CategoryRA = source.CategoryRA

            # Note: We intentionally do NOT copy EvaluationsRC (approval status)
            # New duplicate should start as unapproved

            # Handle owned objects if deep=True
            if deep:
                # Duplicate glosses (MeaningsOC)
                for gloss in source.MeaningsOC:
                    # Use WfiGlossOperations.Duplicate if available, otherwise manually copy
                    gloss_factory = self.project.project.ServiceLocator.GetService(IWfiGlossFactory)
                    new_gloss = gloss_factory.Create()
                    duplicate.MeaningsOC.Add(new_gloss)
                    # Copy gloss form
                    new_gloss.Form.CopyAlternatives(gloss.Form)

                # Duplicate morph bundles (MorphBundlesOS)
                for bundle in source.MorphBundlesOS:
                    # Use WfiMorphBundleOperations.Duplicate if available, otherwise manually copy
                    bundle_factory = self.project.project.ServiceLocator.GetService(IWfiMorphBundleFactory)
                    new_bundle = bundle_factory.Create()
                    duplicate.MorphBundlesOS.Add(new_bundle)
                    # Copy bundle properties
                    new_bundle.Form.CopyAlternatives(bundle.Form)
                    new_bundle.Gloss.CopyAlternatives(bundle.Gloss)
                    if hasattr(bundle, "SenseRA") and bundle.SenseRA:
                        new_bundle.SenseRA = bundle.SenseRA
                    if hasattr(bundle, "MsaRA") and bundle.MsaRA:
                        new_bundle.MsaRA = bundle.MsaRA
                    if hasattr(bundle, "MorphRA") and bundle.MorphRA:
                        new_bundle.MorphRA = bundle.MorphRA
                    if hasattr(bundle, "InflClassRA") and bundle.InflClassRA:
                        new_bundle.InflClassRA = bundle.InflClassRA

            return duplicate

    @OperationsMethod
    def Exists(self, wordform_or_hvo, analysis_or_hvo):
        """
        Check if a specific analysis exists for a wordform.

        Verifies that the given analysis belongs to the specified wordform.

        Args:
            wordform_or_hvo: Either an IWfiWordform object or its HVO
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            bool: True if the analysis exists in the wordform, False otherwise

        Raises:
            FP_NullParameterError: If either parameter is None

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analyses = project.WfiAnalyses.GetAll(wf)
            >>> if analyses:
            ...     # Check if first analysis exists
            ...     exists = project.WfiAnalyses.Exists(wf, analyses[0])
            ...     print(f"Analysis exists: {exists}")
            Analysis exists: True

        Notes:
            - Returns False if wordform has no analyses
            - Checks by comparing HVO values
            - Useful for validation before operations

        See Also:
            GetAll, Create
        """
        self._ValidateParam(wordform_or_hvo, "wordform_or_hvo")
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        wordform = self.__GetWordformObject(wordform_or_hvo)
        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Check if analysis is in wordform's analyses
        for wf_analysis in wordform.AnalysesOC:
            if wf_analysis.Hvo == analysis.Hvo:
                return True

        return False

    # --- Approval & Status Operations ---

    @OperationsMethod
    def GetApprovalStatus(self, analysis_or_hvo):
        """
        Get the approval status of an analysis.

        Returns the current approval status indicating whether the analysis
        has been approved, disapproved, or is still unapproved.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            int: The approval status (from ApprovalStatusTypes enum)
                 0 = DISAPPROVED
                 1 = UNAPPROVED (default)
                 2 = APPROVED

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> status = project.WfiAnalyses.GetApprovalStatus(analysis)
            >>> if status == ApprovalStatusTypes.APPROVED:
            ...     print("This analysis is approved")
            ... elif status == ApprovalStatusTypes.UNAPPROVED:
            ...     print("This analysis needs review")
            ... else:
            ...     print("This analysis is disapproved")

        Notes:
            - New analyses default to UNAPPROVED status
            - Parser-generated analyses may have different initial status
            - Status affects which analysis is used in interlinear text
            - Human approval overrides parser approval

        See Also:
            SetApprovalStatus, IsHumanApproved, IsComputerApproved,
            ApproveAnalysis, RejectAnalysis
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Human evaluations take precedence over parser evaluations.
        # Within the human evaluations, a single approve outweighs
        # disapproves -- matches FLEx UI semantics where one human
        # approval makes the analysis "approved" status.
        #
        # ICmAgentEvaluation exposes two flags: Human (true = human
        # analyst, false = parser) and Approves (true = approves,
        # false = disapproves). The previous implementation treated
        # any non-empty EvaluationsRC as APPROVED, which silently
        # mis-reported DISAPPROVED analyses. (issue #38)
        found_human_disapprove = False
        for evaluation in analysis.EvaluationsRC:
            if not getattr(evaluation, "Human", False):
                continue
            if getattr(evaluation, "Approves", False):
                return ApprovalStatusTypes.APPROVED
            found_human_disapprove = True
        if found_human_disapprove:
            return ApprovalStatusTypes.DISAPPROVED

        return ApprovalStatusTypes.UNAPPROVED

    @OperationsMethod
    def SetApprovalStatus(self, analysis_or_hvo, status):
        """
        Set the approval status of an analysis.

        Updates the approval status to indicate whether the analysis is
        approved, disapproved, or unapproved.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO
            status: The approval status (from ApprovalStatusTypes enum)
                   0 = DISAPPROVED
                   1 = UNAPPROVED
                   2 = APPROVED

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist, status is invalid,
                or no human agents exist in the project

        Example:
            >>> analysis = project.WfiAnalyses.Create(wf)
            >>> # Approve the analysis
            >>> project.WfiAnalyses.SetApprovalStatus(
            ...     analysis, ApprovalStatusTypes.APPROVED)
            >>>
            >>> # Or reject it
            >>> project.WfiAnalyses.SetApprovalStatus(
            ...     analysis, ApprovalStatusTypes.DISAPPROVED)

        Notes:
            - Use ApprovalStatusTypes enum for status values
            - APPROVED analyses are preferred in interlinear text
            - DISAPPROVED analyses are typically hidden
            - UNAPPROVED is the default state
            - Consider using ApproveAnalysis() or RejectAnalysis() shortcuts
            - Creates/updates CmAgentEvaluation objects to persist approval
            - Requires at least one human agent to exist in project
            - Uses first available human agent for evaluation
            - Setting UNAPPROVED removes the evaluation entirely

        See Also:
            GetApprovalStatus, ApproveAnalysis, RejectAnalysis,
            IsHumanApproved
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        if status not in (
            ApprovalStatusTypes.DISAPPROVED,
            ApprovalStatusTypes.UNAPPROVED,
            ApprovalStatusTypes.APPROVED,
        ):
            raise FP_ParameterError(f"Invalid approval status: {status}. Must be 0, 1, or 2.")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Get default human agent for evaluations
        # Import here to avoid circular dependency. AgentOperations lives in
        # the Lists/ subpackage, not TextsWords/ (issue #24).
        from ..Lists.AgentOperations import AgentOperations

        agent_ops = AgentOperations(self.project)

        # Require user to create human agent explicitly (Craig's pattern)
        human_agents = list(agent_ops.GetHumanAgents())
        if not human_agents:
            raise FP_ParameterError(
                "No human agents exist in project. Create one first using "
                "project.Agents.CreateHumanAgent(name, person) before setting approval status."
            )

        # Prefer ILangProject.DefaultUserAgent (the canonical "the user"
        # agent) when it is present and human. AnalyzingAgentsOC has no
        # deterministic ordering, so falling straight back to
        # human_agents[0] would non-deterministically pick whichever
        # human agent the runtime happened to list first -- e.g. a
        # legacy collaborator instead of the actual current user. Fall
        # back to human_agents[0] only when DefaultUserAgent is
        # unavailable or somehow not a human agent. (issue #56)
        agent = None
        default_user = getattr(self.project.lp, "DefaultUserAgent", None)
        if default_user is not None and getattr(default_user, "Human", False):
            for candidate in human_agents:
                if getattr(candidate, "Hvo", None) == getattr(default_user, "Hvo", None):
                    agent = candidate
                    break
            if agent is None:
                # DefaultUserAgent is human but wasn't surfaced by
                # GetHumanAgents() (shouldn't normally happen). Trust
                # the LCM-canonical reference anyway.
                agent = default_user
        if agent is None:
            agent = human_agents[0]

        # Use LCM's purpose-built ICmAgent.SetEvaluation(target, opinion).
        # The previous implementation built ICmAgentEvaluation manually
        # and added it to analysis.EvaluationsRC, but EvaluationsRC is a
        # reference collection (RC) -- adding to it doesn't confer
        # ownership on the new evaluation. ICmAgentEvaluation has to be
        # owned somewhere (it lives under CmAgent.ApprovesOA or in a
        # parallel disapprovals collection), and the manual code set
        # evaluation.Agent on a free-floating object before any owner
        # took it, which trips the Phase 2 NPE pattern. (issue #26)
        #
        # SetEvaluation handles ownership, opinion bookkeeping, and the
        # remove/replace cases internally.
        #
        # Coerce status from True/False/None (user-centric input) or
        # bare-int 0/1/2 (back-compat with the pre-IntEnum constants)
        # to the IntEnum members before dispatching. (issue #59)
        normalized = _coerce_approval_status(status)
        from SIL.LCModel import Opinions

        opinion_map = {
            ApprovalStatusTypes.APPROVED: Opinions.approves,
            ApprovalStatusTypes.DISAPPROVED: Opinions.disapproves,
            ApprovalStatusTypes.UNAPPROVED: Opinions.noopinion,
        }
        agent.SetEvaluation(analysis, opinion_map[normalized])

    @OperationsMethod
    def IsHumanApproved(self, analysis_or_hvo):
        """
        Check if an analysis is human-approved.

        Determines whether a human linguist has explicitly approved this
        analysis (as opposed to parser/computer approval).

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            bool: True if human-approved, False otherwise

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> for analysis in project.WfiAnalyses.GetAll(wf):
            ...     if project.WfiAnalyses.IsHumanApproved(analysis):
            ...         print("Found human-approved analysis")
            ...         glosses = project.WfiAnalyses.GetGlosses(analysis)
            ...         print(f"Glosses: {glosses}")

        Notes:
            - Human approval takes precedence over computer approval
            - New analyses are not human-approved by default
            - Parser-generated analyses require human review
            - Used to distinguish manual vs. automatic analyses
            - Checks for evaluations with human agents and Accepted=True

        See Also:
            IsComputerApproved, ApproveAnalysis, GetApprovalStatus
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # ICmAgentEvaluation always exposes Human (bool) and Approves
        # (bool) per LCM schema; the previous hasattr guards were dead
        # weight. GetApprovalStatus uses the bare property access
        # pattern. (issue #60)
        return any(
            e.Human and e.Approves for e in analysis.EvaluationsRC
        )

    @OperationsMethod
    def IsComputerApproved(self, analysis_or_hvo):
        """
        Check if an analysis is computer/parser-approved.

        Determines whether the parser has approved this analysis
        (as opposed to human approval).

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            bool: True if computer-approved, False otherwise

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> for analysis in project.WfiAnalyses.GetAll(wf):
            ...     if project.WfiAnalyses.IsComputerApproved(analysis):
            ...         print("Parser-generated analysis")
            ...     else:
            ...         print("Needs parsing or manual creation")

        Notes:
            - Computer approval is from the morphological parser
            - Human approval typically overrides computer approval
            - Parser analyses may be approved automatically
            - Useful for identifying parser-generated content
            - Checks for evaluations with Human=False and Approves=True

        See Also:
            IsHumanApproved, GetAgentEvaluation, GetApprovalStatus
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # ICmAgentEvaluation always exposes Human (bool) and Approves
        # (bool) per LCM schema; the previous hasattr guards were dead
        # weight. (issue #60)
        return any(
            not e.Human and e.Approves for e in analysis.EvaluationsRC
        )

    @OperationsMethod
    def ApproveAnalysis(self, analysis_or_hvo):
        """
        Approve an analysis (mark as human-approved).

        Sets the analysis to approved status, indicating that a human
        linguist has reviewed and approved this analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> analysis = project.WfiAnalyses.Create(wf)
            >>> project.WfiAnalyses.AddGloss(analysis, "running", "en")
            >>> # Approve the analysis
            >>> project.WfiAnalyses.ApproveAnalysis(analysis)
            >>> # Verify
            >>> if project.WfiAnalyses.IsHumanApproved(analysis):
            ...     print("Analysis is now approved")

        Notes:
            - This is a convenience method for SetApprovalStatus(APPROVED)
            - Marks the analysis as human-approved
            - Approved analyses are preferred in interlinear text display
            - Only one analysis per wordform should typically be approved
            - Creates CmAgentEvaluation with Accepted=True

        See Also:
            RejectAnalysis, SetApprovalStatus, IsHumanApproved
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Set to approved status
        self.SetApprovalStatus(analysis, ApprovalStatusTypes.APPROVED)

    @OperationsMethod
    def RejectAnalysis(self, analysis_or_hvo):
        """
        Reject an analysis (mark as disapproved).

        Sets the analysis to disapproved status, indicating that this
        analysis is incorrect and should not be used.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> wf = project.Wordforms.Find("running")
            >>> for analysis in project.WfiAnalyses.GetAll(wf):
            ...     # Reject parser analyses that are incorrect
            ...     if project.WfiAnalyses.IsComputerApproved(analysis):
            ...         glosses = project.WfiAnalyses.GetGlosses(analysis)
            ...         if "incorrect_gloss" in glosses:
            ...             project.WfiAnalyses.RejectAnalysis(analysis)

        Notes:
            - This is a convenience method for SetApprovalStatus(DISAPPROVED)
            - Rejected analyses are typically hidden in FLEx UI
            - Use instead of Delete to preserve analysis history
            - Useful for marking parser errors
            - Creates CmAgentEvaluation with Accepted=False

        See Also:
            ApproveAnalysis, SetApprovalStatus, Delete
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Set to disapproved status
        self.SetApprovalStatus(analysis, ApprovalStatusTypes.DISAPPROVED)

    # --- Gloss Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetGlosses(self, analysis_or_hvo):
        """
        Get all glosses for an analysis.

        Retrieves all IWfiGloss objects associated with this analysis,
        representing the meanings/translations of the analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            list: List of IWfiGloss objects

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> glosses = project.WfiAnalyses.GetGlosses(analysis)
            >>> for gloss in glosses:
            ...     # Access gloss properties
            ...     print(f"Gloss HVO: {gloss.Hvo}")

        Notes:
            - Returns empty list if analysis has no glosses
            - Glosses are stored in the MeaningsOC collection
            - Each gloss can have text in multiple writing systems
            - Typically one gloss per analysis, but multiple are possible

        See Also:
            GetGlossCount, AddGloss
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        return list(analysis.MeaningsOC)

    @OperationsMethod
    def GetGlossCount(self, analysis_or_hvo):
        """
        Get the count of glosses for an analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            int: Number of glosses in the analysis

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> count = project.WfiAnalyses.GetGlossCount(analysis)
            >>> print(f"Analysis has {count} gloss(es)")
            Analysis has 1 gloss(es)

        Notes:
            - Returns 0 if analysis has no glosses
            - Most analyses have exactly one gloss
            - Multiple glosses may represent different writing systems

        See Also:
            GetGlosses, AddGloss
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        return analysis.MeaningsOC.Count

    @OperationsMethod
    def AddGloss(self, analysis_or_hvo, gloss_text, wsHandle=None):
        """
        Add a gloss to an analysis.

        Creates a new IWfiGloss object with the specified text and adds it
        to the analysis's gloss collection.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO
            gloss_text: The gloss text to add
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            IWfiGloss: The newly created gloss object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If analysis_or_hvo or gloss_text is None
            FP_ParameterError: If analysis doesn't exist or gloss_text is empty

        Example:
            >>> analysis = project.WfiAnalyses.Create(wf)
            >>> # Add English gloss
            >>> gloss = project.WfiAnalyses.AddGloss(analysis, "running", "en")
            >>> # Add French gloss
            >>> gloss_fr = project.WfiAnalyses.AddGloss(analysis, "courir", "fr")
            >>> # Verify
            >>> count = project.WfiAnalyses.GetGlossCount(analysis)
            >>> print(f"Analysis now has {count} glosses")

        Notes:
            - Gloss text is stored in the specified writing system
            - Multiple glosses can exist for different writing systems
            - Empty or whitespace-only gloss text raises error
            - Glosses are stored in the MeaningsOC collection

        See Also:
            GetGlosses, GetGlossCount
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")
        self._ValidateParam(gloss_text, "gloss_text")

        if not gloss_text or not gloss_text.strip():
            raise FP_ParameterError("Gloss text cannot be empty")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM("Add gloss"):
            # Create the gloss using the factory
            factory = self.project.project.ServiceLocator.GetService(IWfiGlossFactory)
            new_gloss = factory.Create()

            # Add to analysis's meanings collection (must be done before setting properties)
            analysis.MeaningsOC.Add(new_gloss)

            # Set the gloss text
            mkstr = TsStringUtils.MakeString(gloss_text, wsHandle)
            new_gloss.Form.set_String(wsHandle, mkstr)

            return new_gloss

    # --- Morph Bundle Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetMorphBundles(self, analysis_or_hvo):
        """
        Get all morpheme bundles for an analysis.

        Retrieves all IWfiMorphBundle objects representing the morphological
        breakdown of the wordform in this analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            list: List of IWfiMorphBundle objects in sequence order

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> bundles = project.WfiAnalyses.GetMorphBundles(analysis)
            >>> for bundle in bundles:
            ...     # Access bundle properties
            ...     print(f"Morph bundle HVO: {bundle.Hvo}")

        Notes:
            - Returns empty list if analysis has no morph bundles
            - Bundles are ordered sequence (MorphBundlesOS)
            - Each bundle represents one morpheme in the analysis
            - Bundles include morph form, gloss, and grammatical info

        See Also:
            GetMorphBundleCount
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        return list(analysis.MorphBundlesOS)

    @OperationsMethod
    def GetMorphBundleCount(self, analysis_or_hvo):
        """
        Get the count of morpheme bundles for an analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            int: Number of morph bundles in the analysis

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> count = project.WfiAnalyses.GetMorphBundleCount(analysis)
            >>> print(f"Analysis has {count} morpheme(s)")
            Analysis has 2 morpheme(s)

        Notes:
            - Returns 0 if analysis has no morph bundles
            - Count represents the morphological complexity
            - Monomorphemic words typically have 1 bundle
            - Polymorphemic words have multiple bundles

        See Also:
            GetMorphBundles
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        return analysis.MorphBundlesOS.Count

    # --- Category Operations ---

    @OperationsMethod
    def GetCategory(self, analysis_or_hvo):
        """
        Get the grammatical category (part of speech) for an analysis.

        Retrieves the IPartOfSpeech object representing the grammatical
        category assigned to this analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            IPartOfSpeech or None: The category object, or None if not set

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> category = project.WfiAnalyses.GetCategory(analysis)
            >>> if category:
            ...     name = project.POS.GetName(category)
            ...     abbr = project.POS.GetAbbreviation(category)
            ...     print(f"Category: {name} ({abbr})")
            Category: Verb (V)

        Notes:
            - Returns None if no category is set
            - Category represents the overall POS for the wordform
            - Individual morph bundles may have different categories
            - Use project.POS methods to access category properties

        See Also:
            SetCategory, GetMorphBundles
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        if hasattr(analysis, "CategoryRA") and analysis.CategoryRA:
            return analysis.CategoryRA

        return None

    @OperationsMethod
    def SetCategory(self, analysis_or_hvo, category):
        """
        Set the grammatical category (part of speech) for an analysis.

        Assigns a grammatical category to the analysis, indicating the
        overall part of speech for the wordform.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO
            category: IPartOfSpeech object to set as the category

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If analysis_or_hvo or category is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = project.WfiAnalyses.Create(wf)
            >>> # Find or create a verb category
            >>> verb = project.POS.Find("Verb")
            >>> if verb:
            ...     project.WfiAnalyses.SetCategory(analysis, verb)
            >>> # Verify
            >>> cat = project.WfiAnalyses.GetCategory(analysis)
            >>> print(project.POS.GetName(cat))
            Verb

        Notes:
            - Category must be a valid IPartOfSpeech object
            - Use project.POS methods to find/create categories
            - Setting to None will clear the category
            - Category affects grammatical analysis display

        See Also:
            GetCategory, project.POS.Find, project.POS.Create
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")
        self._ValidateParam(category, "category")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Verify category is a valid IPartOfSpeech
        if not isinstance(category, IPartOfSpeech):
            raise FP_ParameterError("Category must be an IPartOfSpeech object")

        # Set the category
        if hasattr(analysis, "CategoryRA"):
            analysis.CategoryRA = category
        else:
            raise FP_ParameterError("Analysis does not support CategoryRA property")

    # --- Evaluation Operations ---

    @OperationsMethod
    def GetAgentEvaluation(self, analysis_or_hvo):
        """
        Get the parser/agent evaluation for an analysis.

        Retrieves evaluation information created by the parser or other
        automated agents.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            ICmAgentEvaluation or None: The agent evaluation object, or None if not set

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> evaluation = project.WfiAnalyses.GetAgentEvaluation(analysis)
            >>> if evaluation:
            ...     print("Analysis has parser evaluation")
            ... else:
            ...     print("No parser evaluation")

        Notes:
            - Returns None if no agent evaluation exists
            - Agent evaluations are created by the parser
            - Multiple evaluations may exist in EvaluationsRC
            - This returns the first evaluation found

        See Also:
            GetHumanEvaluation, IsComputerApproved
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Return the first PARSER evaluation (Human == False). The
        # previous implementation returned EvaluationsRC[0], but
        # EvaluationsRC mixes human and parser evaluations and LCM
        # ordering is not deterministic -- so that path would
        # non-deterministically return a human evaluation when one
        # happened to be listed first. Mirrors the discriminating
        # iteration pattern used in GetApprovalStatus. (issue #55)
        for evaluation in analysis.EvaluationsRC:
            if not getattr(evaluation, "Human", True):
                return evaluation

        return None

    @OperationsMethod
    def GetHumanEvaluation(self, analysis_or_hvo):
        """
        Get the human evaluation for an analysis.

        Retrieves evaluation information created by human linguists.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            ICmAgentEvaluation or None: The human evaluation object, or None if not set

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> evaluation = project.WfiAnalyses.GetHumanEvaluation(analysis)
            >>> if evaluation:
            ...     print("Analysis has human evaluation")
            ... else:
            ...     print("Analysis not yet reviewed by human")

        Notes:
            - Returns None if no human evaluation exists
            - Human evaluations indicate manual review
            - Searches EvaluationsRC for human agent
            - Human evaluation overrides parser evaluation

        See Also:
            GetAgentEvaluation, IsHumanApproved
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Return the first HUMAN evaluation (Human == True). The
        # previous implementation accepted any evaluation that exposed
        # an .Agent attribute, but every ICmAgentEvaluation has an
        # Agent -- the check did not actually discriminate. Mirrors
        # the iteration pattern used in GetApprovalStatus. (issue #55)
        for evaluation in analysis.EvaluationsRC:
            if getattr(evaluation, "Human", False):
                return evaluation

        return None

    @OperationsMethod
    def GetEvaluations(self, analysis_or_hvo):
        """
        Get all agent evaluations for an analysis.

        Retrieves all ICmAgentEvaluation objects from the analysis's
        EvaluationsRC (Reference Collection). This is a read-only property
        that returns evaluations created by both human linguists and automated
        agents (e.g., morphological parser).

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            list: List of ICmAgentEvaluation objects. Returns empty list if
                no evaluations exist.

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> evaluations = project.WfiAnalyses.GetEvaluations(analysis)
            >>> for evaluation in evaluations:
            ...     if hasattr(evaluation, 'Agent') and evaluation.Agent:
            ...         agent_name = evaluation.Agent.Name.BestAnalysisAlternative.Text
            ...         is_accepted = evaluation.Accepted if hasattr(evaluation, 'Accepted') else None
            ...         print(f"Agent: {agent_name}, Accepted: {is_accepted}")

        Notes:
            - This is a READ-ONLY property (Reference Collection)
            - Returns all evaluations (human and computer/parser)
            - Empty list indicates no evaluations have been created
            - Evaluations track approval/disapproval status
            - Each evaluation links to an ICmAgent (human or parser)
            - Use IsHumanApproved() or IsComputerApproved() for simple checks
            - Evaluations are added/removed via SetApprovalStatus()

        See Also:
            GetAgentEvaluation, GetHumanEvaluation, IsHumanApproved,
            IsComputerApproved, SetApprovalStatus
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        return list(analysis.EvaluationsRC)

    # --- Utility Operations ---

    @OperationsMethod
    def GetOwningWordform(self, analysis_or_hvo):
        """
        Get the wordform that owns this analysis.

        Retrieves the IWfiWordform object that contains this analysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            IWfiWordform: The owning wordform object

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> wordform = project.WfiAnalyses.GetOwningWordform(analysis)
            >>> form = project.Wordforms.GetForm(wordform)
            >>> print(f"Analysis belongs to: {form}")
            Analysis belongs to: running

        Notes:
            - Every analysis must have an owning wordform
            - This is the inverse of GetAll(wordform)
            - Useful for navigating from analysis back to wordform

        See Also:
            GetAll, project.Wordforms.GetForm
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Cast to declared return type IWfiWordform. Raw analysis.Owner is
        # typed as ICmObject in LCM; pythonnet only surfaces IWfiWordform
        # properties (e.g. AnalysesOC, Form) after the explicit interface cast.
        return IWfiWordform(analysis.Owner)

    @OperationsMethod
    def GetGuid(self, analysis_or_hvo):
        """
        Get the GUID (globally unique identifier) of an analysis.

        Retrieves the unique identifier for this analysis object.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or its HVO

        Returns:
            System.Guid: The GUID of the analysis

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None
            FP_ParameterError: If analysis doesn't exist

        Example:
            >>> analysis = analyses[0]
            >>> guid = project.WfiAnalyses.GetGuid(analysis)
            >>> print(f"Analysis GUID: {guid}")
            Analysis GUID: a1b2c3d4-e5f6-7890-abcd-ef1234567890

        Notes:
            - GUID is a globally unique identifier
            - Persists across sessions
            - Useful for external references
            - Different from HVO (database handle)

        See Also:
            GetOwningWordform
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        return analysis.Guid
