#
#   MSAOperations.py
#
#   Class: MSAOperations
#          Morphosyntactic-analysis (MSA) creation operations for FieldWorks
#          Language Explorer projects via SIL Language and Culture Model
#          (LCM) API.
#
#          Pairs with morphosyntax_analysis.py (the reading wrapper) and
#          msa_collection.py (iteration). This module handles the creation
#          + attach side of the four concrete MSA types:
#          - MoStemMsa (kStem) -- stem entries, takes one POS
#          - MoDerivAffMsa (kDeriv) -- derivational affixes, from-POS + to-POS
#          - MoInflAffMsa (kInfl) -- inflectional affixes, POS + slots
#          - MoUnclassifiedAffixMsa (kUnclassified) -- catch-all affix
#
#          All four use the same idiom: build a SandboxGenericMSA with the
#          MsaType + POS info, call the type-specific factory's
#          Create(sense.Owner, sandbox) overload, then attach via
#          sense.MorphoSyntaxAnalysisRA.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

# Import BaseOperations parent class
from ..Shared.arg_checks import require_lcm_object
from ..BaseOperations import BaseOperations, OperationsMethod

# Import FLEx LCM types
from SIL.LCModel import (
    ICmPossibility,
    IMoStemMsa,
    IMoStemMsaFactory,
    IMoDerivAffMsa,
    IMoDerivAffMsaFactory,
    IMoInflAffMsa,
    IMoInflAffMsaFactory,
    IMoUnclassifiedAffixMsa,
    IMoUnclassifiedAffixMsaFactory,
    ILexSense,
    ILexEntry,
    ILexEntryRepository,
    IWfiMorphBundleRepository,
    LexEntryTags,
    MsaType,
)
from SIL.LCModel.DomainServices import SandboxGenericMSA

import clr

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
    FP_ReadOnlyError,
    FP_NullParameterError,
)

# Import the read-side wrapper + smart collection this module's GetAll
# hands back. Both already existed in full (morphosyntax_analysis.py,
# msa_collection.py); GetAll is the call path that finally instantiates
# them, so the subtype differences between the four concrete MSA classes
# stay behind the wrapper's is_* / as_* / pos_* families rather than
# reaching the caller as a ClassName test or a cast (Principle VI).
from .morphosyntax_analysis import MorphosyntaxAnalysis
from .msa_collection import MSACollection
from ..Shared.feature_struc_utils import c4_to_feat_struc_spec

# Concrete-interface cast for HVO/object resolution of inflection classes
# (issue #573): project.Object(hvo) returns a bare ICmObject; InflectionClassRA
# membership checks and the ClassName gate need the MoInflClass view.
from ..lcm_casting import cast_to_concrete


# --- Structured result for RemoveOrphaned (issue #206) ----------------------
# Follows the namedtuple-with-docstring convention used elsewhere in this
# codebase for multi-value structured results (see
# LocalizedListsOperations.ImportLocalizedListsResult).

RemovedMSA = namedtuple("RemovedMSA", ("entry_hvo", "msa_hvo", "class_name"))
RemovedMSA.__doc__ = """
One MSA removed by MSAOperations.RemoveOrphaned.

Fields:
    entry_hvo (int): Hvo of the owning ILexEntry the MSA was removed from.
    msa_hvo (int): Hvo of the removed MSA.
    class_name (str): ClassName of the removed MSA (e.g. "MoStemMsa").
"""

EntryOrphanBreakdown = namedtuple(
    "EntryOrphanBreakdown", ("entry_hvo", "removed_count", "kept_count")
)
EntryOrphanBreakdown.__doc__ = """
Per-entry breakdown produced by MSAOperations.RemoveOrphaned.

Fields:
    entry_hvo (int): Hvo of the scanned ILexEntry.
    removed_count (int): Number of orphaned MSAs removed from this
        entry's MorphoSyntaxAnalysesOC.
    kept_count (int): Number of MSAs in this entry's MorphoSyntaxAnalysesOC
        that were still referenced (by an entry-local sense or a
        project-wide morph bundle) and therefore kept.
"""

RemoveOrphanedResult = namedtuple(
    "RemoveOrphanedResult",
    ("removed_count", "kept_count", "removed", "by_entry"),
)
RemoveOrphanedResult.__doc__ = """
Structured result for MSAOperations.RemoveOrphaned.

Fields:
    removed_count (int): Total number of orphaned MSAs removed.
    kept_count (int): Total number of MSAs examined that were still
        referenced (by an entry-local sense's MorphoSyntaxAnalysisRA, or
        project-wide by an IWfiMorphBundle.MsaRA) and therefore kept.
    removed (list[RemovedMSA]): One entry per MSA actually removed.
    by_entry (list[EntryOrphanBreakdown]): One entry per scanned
        ILexEntry that owned at least one MSA, summarising removed/kept
        counts for that entry. Entries with an empty
        MorphoSyntaxAnalysesOC are omitted.
"""


class MSAOperations(BaseOperations):
    """
    Read, creation and attach operations for morphosyntactic analyses (MSAs).

    A LexSense's grammatical analysis lives in
    ``sense.MorphoSyntaxAnalysisRA``, which is a reference to an MSA owned
    by ``sense.Entry.MorphoSyntaxAnalysesOC``. LCM offers four concrete
    MSA subtypes that share IMoMorphSynAnalysis as base; each subtype has
    its own factory whose 2-arg Create overload takes an owner (the sense's
    entry) and a SandboxGenericMSA descriptor.

    This wrapper hides the ServiceLocator + SandboxGenericMSA dance and
    auto-attaches the new MSA to the sense; ``GetAll`` covers the reading
    direction, handing back MorphosyntaxAnalysis wrappers in an
    MSACollection so subtype differences never reach the caller.

    Usage::

        from flexicon import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        entry = list(project.LexiconAllEntries())[0]
        sense = entry.SensesOS[0]

        # Read: every MSA owned by the entry, already wrapped.
        for msa in project.MSA.GetAll(entry):
            if msa.is_deriv_aff_msa:
                print(msa.pos_from, "->", msa.pos_to)

        # Stem MSA (most common case): assign POS to a lexical entry.
        verb_pos = project.POS.Find("Verb")
        project.MSA.CreateStem(sense, verb_pos)

        # Derivational affix: noun -> verb
        n_pos = project.POS.Find("Noun")
        v_pos = project.POS.Find("Verb")
        project.MSA.CreateDerivAff(sense, from_pos=n_pos, to_pos=v_pos)

    See Also:
        morphosyntax_analysis.MorphosyntaxAnalysis (reading)
        msa_collection.MSACollection (iteration)
    """

    def __init__(self, project):
        super().__init__(project)

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    @OperationsMethod
    def GetAll(self, entry_or_hvo=None):
        """
        Get every morphosyntactic analysis owned by an entry, or by the
        whole project.

        Reads ``entry.MorphoSyntaxAnalysesOC`` and returns a smart
        collection of wrapped MSA objects that transparently handle the
        four concrete subtypes (MoStemMsa, MoDerivAffMsa, MoInflAffMsa,
        MoUnclassifiedAffixMsa). The caller never tests ``ClassName`` and
        never casts: subtype differences are reached through the
        wrapper's ``is_*`` / ``as_*`` / ``pos_*`` families instead.

        Args:
            entry_or_hvo: The ILexEntry object or HVO whose
                MorphoSyntaxAnalysesOC should be read. Pass None (the
                default) to sweep every entry in the project.

        Returns:
            MSACollection[MorphosyntaxAnalysis]: Smart collection of
                MorphosyntaxAnalysis wrapper objects, showing a subtype
                breakdown on ``str()`` and supporting filtered queries.
                Empty collection if the entry owns no MSAs.

        Raises:
            FP_ParameterError: If entry_or_hvo is supplied but does not
                resolve to a valid ILexEntry.

        Example:
            >>> entry = list(project.LexiconAllEntries())[0]
            >>>
            >>> # Every MSA on one entry
            >>> msas = project.MSA.GetAll(entry)
            >>> print(msas)  # Shows subtype breakdown
            # MSACollection (3 total)
            #   MoStemMsa: 2 (66%)
            #   MoDerivAffMsa: 1 (33%)
            >>>
            >>> # Iterate the wrapped objects -- no ClassName, no cast
            >>> for msa in msas:
            ...     if msa.is_deriv_aff_msa:
            ...         print(msa.pos_from, "->", msa.pos_to)
            ...     else:
            ...         print(msa.pos_main)
            >>>
            >>> # len() and indexing work directly on the collection
            >>> print(len(msas))
            3
            >>> first = msas[0]
            >>>
            >>> # Filter by subtype, or by POS, and chain the two
            >>> verb_pos = project.POS.Find("Verb")
            >>> verb_stems = project.MSA.GetAll(entry).filter(pos_main=verb_pos)
            >>>
            >>> # Project-wide sweep
            >>> all_msas = project.MSA.GetAll()
            >>> print(f"Project has {len(all_msas)} MSAs")

        Notes:
            - Wiring, not new design. MorphosyntaxAnalysis
              (morphosyntax_analysis.py) and MSACollection
              (msa_collection.py) were already complete; this accessor is
              the call path that instantiates them.
            - Deliberately NOT decorated with ``@wrap_enumerable``, unlike
              most GetAll methods in this library. That decorator adapts
              return values that lack sequence behavior -- a raw C#
              IEnumerable or a bare Python generator. ``MSACollection``
              already supplies ``__len__``, ``__getitem__`` (including
              slicing) and ``__iter__`` through SmartCollection, so
              ``_needs_enumerable_wrap`` (BaseOperations.py) returns False
              for it and the decorator would be an inert no-op that
              falsely implied the result needed adapting. The behavioral
              collection contract -- loop it, ``len()`` it, index it,
              re-iterate it -- is met in full, by MSACollection itself.
            - This method performs no write and does not require a
              write-enabled project. That is a property of this method,
              not of MSAOperations: the class is write-capable, and its
              CreateStem / CreateDerivAff / CreateInflAff /
              CreateUnclassifiedAffix / SetStemMsaPos / SetDerivAffMsaPos
              / SetInflAffMsaSlots / GetInflAffMsaSlots / ChangeAffixVariant
              / RemoveOrphaned
              siblings all mutate
              the project and call _EnsureWriteEnabled.
            - Collection order follows FLEx's MorphoSyntaxAnalysesOC
              order. When entry_or_hvo is None, entries are visited in
              ILexEntryRepository order and each entry's MSAs are
              appended in turn.
            - An entry's MorphoSyntaxAnalysesOC can contain an MSA no
              sense currently points at; GetAll reports what the entry
              owns, and does not filter orphans. Use RemoveOrphaned to
              prune them.
            - ``ILexEntry.MorphoSyntaxAnalysesOC`` is
              ``ILcmOwningCollection<IMoMorphSynAnalysis>``, read-only,
              per tests/contract/snapshots/liblcm_baseline.json
              (liblcm 11.0.0.0).
            - Items can be passed straight back into other MSAOperations
              methods (e.g. ``ChangeAffixVariant(item, ...)``) -- resolvers
              unwrap the wrapper internally (issue #449). A caller
              performing a direct pythonnet cast, e.g. ``IMoInflAffMsa(item)``,
              must use ``item.lcm_object`` instead
              (``IMoInflAffMsa(item.lcm_object)``), since pythonnet cannot
              cast a Python wrapper instance.

        See Also:
            CreateStem, CreateDerivAff, CreateInflAff,
            CreateUnclassifiedAffix, RemoveOrphaned,
            morphosyntax_analysis.MorphosyntaxAnalysis,
            msa_collection.MSACollection
        """
        analyses = []

        if entry_or_hvo is None:
            entries = self.project.ObjectsIn(ILexEntryRepository)
        else:
            entries = [self.__ResolveEntry(entry_or_hvo)]

        for entry_obj in entries:
            for msa in entry_obj.MorphoSyntaxAnalysesOC:
                analyses.append(MorphosyntaxAnalysis(msa))

        return MSACollection(analyses)

    # ------------------------------------------------------------------
    # Creation + attach
    # ------------------------------------------------------------------

    @OperationsMethod
    def CreateStem(self, sense, pos):
        """
        Create an IMoStemMsa, attach it to the sense.

        Args:
            sense: An ILexSense (or HVO) to attach the MSA to.
            pos: An IPartOfSpeech (or HVO) -- the grammatical category, or
                None to leave PartOfSpeechRA unset. Passing None is valid and
                means "grammatical category not specified" -- a very common
                state for stem entries in FLEx (the category cell is blank).

                BEHAVIOR CHANGE (issue: null-category stems): previously a None
                pos raised FP_NullParameterError, which made it impossible to
                round-trip a legitimately category-less stem MSA. This mirrors
                CreateDerivAff's to_pos=None "unset" precedent.

        Returns:
            IMoStemMsa: The newly created and attached MSA.

        Raises:
            FP_ReadOnlyError, FP_NullParameterError, FP_ParameterError.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(sense, "sense")
        # pos intentionally not validated -- None is a legal "unset" value.

        sense_obj = self.__ResolveSense(sense)
        pos_obj = self.__Resolve(pos) if pos is not None else None

        sandbox = SandboxGenericMSA()
        sandbox.MsaType = MsaType.kStem
        sandbox.MainPOS = pos_obj

        new_msa = self.__CreateAndAttach(
            sense_obj, sandbox, IMoStemMsaFactory
        )
        return IMoStemMsa(new_msa)

    @OperationsMethod
    def CreateDerivAff(self, sense, from_pos, to_pos=None):
        """
        Create an IMoDerivAffMsa, attach it to the sense.

        Args:
            sense: An ILexSense (or HVO) to attach the MSA to.
            from_pos: An IPartOfSpeech the affix attaches to (input category).
            to_pos: An IPartOfSpeech the affix produces (output category), or
                None to leave ToPartOfSpeechRA unset. Passing None is valid
                and means "output category not yet determined" -- the user can
                fill this in later via MSA.SetDerivAffMsaPos(sense, to_pos=X).

                BEHAVIOR CHANGE (Cycle 4, issue #91): Previously the default
                was to copy from_pos when to_pos was omitted, producing a
                linguistically invalid "derivation that doesn't change
                category". The default is now None (unset), which is the
                correct state for an incompletely specified derivational affix.

        Returns:
            IMoDerivAffMsa: The newly created and attached MSA.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(sense, "sense")
        self._ValidateParam(from_pos, "from_pos")
        # to_pos intentionally not validated -- None is a legal "unset" value.

        sense_obj = self.__ResolveSense(sense)
        from_pos_obj = self.__Resolve(from_pos)
        to_pos_obj = self.__Resolve(to_pos) if to_pos is not None else None

        sandbox = SandboxGenericMSA()
        sandbox.MsaType = MsaType.kDeriv
        sandbox.MainPOS = from_pos_obj
        sandbox.SecondaryPOS = to_pos_obj

        new_msa = self.__CreateAndAttach(
            sense_obj, sandbox, IMoDerivAffMsaFactory
        )
        deriv = IMoDerivAffMsa(new_msa)
        # Explicitly set ToPartOfSpeechRA after creation: SandboxGenericMSA's
        # SecondaryPOS mapping may not reliably clear the field when None is
        # passed, so we set it directly to ensure the unset state is stored.
        # __CreateAndAttach has its own bracket which has already committed by
        # here, so this follow-up write needs a transaction of its own (D6).
        with self._TransactionCM("Set derivational affix output category"):
            deriv.ToPartOfSpeechRA = to_pos_obj
        return deriv

    @OperationsMethod
    def CreateInflAff(self, sense, pos, slots=None):
        """
        Create an IMoInflAffMsa, attach it to the sense.

        Args:
            sense: An ILexSense (or HVO) to attach the MSA to.
            pos: An IPartOfSpeech -- the category this affix inflects, or None
                to leave PartOfSpeechRA unset. Passing None is valid and means
                "category not yet specified": an inflectional affix MSA may
                legitimately carry a blank category cell in FLEx. Mirrors
                CreateStem's / CreateUnclassifiedAffix's pos=None support.
            slots: Optional sequence of IMoInflAffixSlot objects. Slots
                are added to the MSA's SlotsRC reference collection
                after creation (Phase 2 ownership-ordering doesn't apply
                to reference collections).

        Returns:
            IMoInflAffMsa: The newly created and attached MSA.

        Note:
            HermitCrab uses ``IMoInflAffixSlot`` (template slots) to
            constrain which inflection classes of the target POS an
            affix is valid for. If the language uses inflection classes
            AND the target slot has class restrictions, HermitCrab will
            reject analyses where the MSA is not wired into a slot
            whose ``InflectionClassesRC`` matches the stem's class.
            Populate ``slots`` here, then configure each slot's
            ``InflectionClassesRC`` separately. Languages without
            inflection classes do not need slot-level class
            restrictions.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(sense, "sense")
        # pos intentionally not validated -- None is a legal "unset" value
        # (a category-less inflectional affix). Mirrors CreateUnclassifiedAffix.

        sense_obj = self.__ResolveSense(sense)
        pos_obj = self.__Resolve(pos) if pos is not None else None

        sandbox = SandboxGenericMSA()
        sandbox.MsaType = MsaType.kInfl
        sandbox.MainPOS = pos_obj

        with self._TransactionCM("Create inflectional affix MSA"):
            new_msa = self.__CreateAndAttach(
                sense_obj, sandbox, IMoInflAffMsaFactory
            )
            new_msa = IMoInflAffMsa(new_msa)

            if slots:
                for slot in slots:
                    resolved = self.__Resolve(slot)
                    new_msa.SlotsRC.Add(resolved)

            return new_msa

    @OperationsMethod
    def CreateUnclassifiedAffix(self, sense, pos):
        """
        Create an IMoUnclassifiedAffixMsa, attach it to the sense.

        Args:
            sense: An ILexSense (or HVO) to attach the MSA to.
            pos: An IPartOfSpeech (or HVO) -- the grammatical category, or None
                to leave PartOfSpeechRA unset. Passing None is valid and means
                "category not specified" -- an unclassified affix legitimately
                may carry no grammatical category (that is what "unclassified"
                means). Mirrors CreateStem's / CreateDerivAff's pos=None support.

        Returns:
            IMoUnclassifiedAffixMsa: The newly created and attached MSA.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(sense, "sense")
        # pos intentionally not validated -- None is a legal "unset" value.

        sense_obj = self.__ResolveSense(sense)
        pos_obj = self.__Resolve(pos) if pos is not None else None

        sandbox = SandboxGenericMSA()
        sandbox.MsaType = MsaType.kUnclassified
        sandbox.MainPOS = pos_obj

        new_msa = self.__CreateAndAttach(
            sense_obj, sandbox, IMoUnclassifiedAffixMsaFactory
        )
        return IMoUnclassifiedAffixMsa(new_msa)

    @OperationsMethod
    def SetStemMsaPos(self, sense, pos, keep_inflection_class=True):
        """
        Update the POS on an existing IMoStemMsa attached to a sense.

        If the sense has no MSA, or if its MSA isn't a stem MSA, raises
        FP_ParameterError. For type conversion (e.g. stem -> deriv-aff)
        the caller should create a new MSA via CreateStem / CreateDerivAff;
        in-place conversion across MSA types is intentionally not
        supported by this wrapper because LCM doesn't expose a clean
        idiom for it.

        Args:
            sense: An ILexSense whose MSA should be updated.
            pos: New IPartOfSpeech (or HVO) for the stem.
            keep_inflection_class: When True (the default), the stem MSA's
                existing ``InflectionClassRA`` is restored after the POS
                change if it still belongs to the new POS or its parent
                chain (issue #573). When the old class is not valid for
                the new POS, a warning is logged and the class is left
                cleared rather than attaching an incompatible class.
                Pass False to always drop the inflection class with the
                POS change.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(sense, "sense")
        self._ValidateParam(pos, "pos")

        sense_obj = self.__ResolveSense(sense)
        existing = sense_obj.MorphoSyntaxAnalysisRA
        if existing is None:
            raise FP_ParameterError(
                "Sense has no MSA; use CreateStem to create one."
            )
        try:
            stem = IMoStemMsa(existing)
        except Exception:
            raise FP_ParameterError(
                "Sense's existing MSA is not a stem MSA. To change MSA "
                "type, create a new MSA with the appropriate Create* method."
            )

        # Resolution stays outside the bracket so an unresolvable POS raises
        # before a named undo entry is opened (D5).
        pos_obj = self.__Resolve(pos)

        # Capture the old inflection class before the POS change drops it
        # (issue #573). Validation against the NEW POS happens inside the
        # bracket so the restore is atomic with the POS write.
        old_infl_class = None
        if keep_inflection_class:
            old_infl_class = getattr(stem, "InflectionClassRA", None)

        with self._TransactionCM("Set stem MSA POS"):
            stem.PartOfSpeechRA = pos_obj
            if old_infl_class is not None:
                if int(old_infl_class.Hvo) in self.__PosChainInflectionClassHvos(
                    pos_obj
                ):
                    stem.InflectionClassRA = old_infl_class
                else:
                    logger.warning(
                        "SetStemMsaPos: inflection class %r is not valid "
                        "for the new part of speech %r; leaving the "
                        "inflection class cleared.",
                        self.__PossibilityLabel(old_infl_class),
                        self.__PossibilityLabel(pos_obj),
                    )

    @OperationsMethod
    def SetDerivAffMsaPos(self, sense, from_pos=None, to_pos=None):
        """
        Update the from-POS and/or to-POS on an existing IMoDerivAffMsa
        attached to a sense.

        If the sense has no MSA, or if its MSA isn't a derivational-affix
        MSA, raises FP_ParameterError. At least one of from_pos or to_pos
        must be supplied.

        Args:
            sense: An ILexSense whose MSA should be updated.
            from_pos: New IPartOfSpeech (or HVO) for the input category
                (FromPartOfSpeechRA). Pass None to leave unchanged.
            to_pos: New IPartOfSpeech (or HVO) for the output category
                (ToPartOfSpeechRA). Pass None to leave unchanged.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(sense, "sense")

        if from_pos is None and to_pos is None:
            raise FP_ParameterError(
                "At least one of from_pos or to_pos must be supplied."
            )

        sense_obj = self.__ResolveSense(sense)
        existing = sense_obj.MorphoSyntaxAnalysisRA
        if existing is None:
            raise FP_ParameterError(
                "Sense has no MSA; use CreateDerivAff to create one."
            )
        try:
            deriv = IMoDerivAffMsa(existing)
        except Exception:
            raise FP_ParameterError(
                "Sense's existing MSA is not a derivational-affix MSA. To "
                "change MSA type, create a new MSA with the appropriate "
                "Create* method."
            )

        with self._TransactionCM("Set derivational affix MSA POS"):
            if from_pos is not None:
                deriv.FromPartOfSpeechRA = self.__Resolve(from_pos)
            if to_pos is not None:
                deriv.ToPartOfSpeechRA = self.__Resolve(to_pos)

    @OperationsMethod
    def SetInflAffMsaSlots(self, sense, slots, replace=True):
        """
        Update the ``SlotsRC`` reference collection on an existing
        ``IMoInflAffMsa`` attached to a sense.

        ``CreateInflAff`` accepts ``slots=`` only at creation time; this
        method edits slot membership on an MSA that already exists.

        Args:
            sense: An ``ILexSense`` (or HVO) whose inflectional-affix MSA
                should be updated.
            slots: Sequence of ``IMoInflAffixSlot`` objects (or HVOs) to
                attach. An empty sequence with ``replace=True`` clears all
                slots.
            replace: When ``True`` (default), existing slots are cleared
                before the new set is added. When ``False``, each resolved
                slot is appended without clearing.

        Raises:
            FP_ReadOnlyError, FP_NullParameterError, FP_ParameterError.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(sense, "sense")
        self._ValidateParam(slots, "slots")

        sense_obj = self.__ResolveSense(sense)
        existing = sense_obj.MorphoSyntaxAnalysisRA
        if existing is None:
            raise FP_ParameterError(
                "Sense has no MSA; use CreateInflAff to create one."
            )
        try:
            infl = IMoInflAffMsa(existing)
        except Exception:
            raise FP_ParameterError(
                "Sense's existing MSA is not an inflectional-affix MSA. To "
                "change MSA type, create a new MSA with the appropriate "
                "Create* method."
            )

        resolved_slots = [self.__Resolve(slot) for slot in slots]

        with self._TransactionCM("Set inflectional affix MSA slots"):
            if replace:
                infl.SlotsRC.Clear()
            for slot_obj in resolved_slots:
                infl.SlotsRC.Add(slot_obj)

    @OperationsMethod
    def GetInflAffMsaSlots(self, sense_or_msa):
        """
        Read ``SlotsRC`` on an inflectional-affix MSA.

        This is the read-side pair for ``SetInflAffMsaSlots``. Pass either
        the sense whose ``MorphoSyntaxAnalysisRA`` should be read, or the
        inflectional-affix MSA (or its HVO) directly.

        Args:
            sense_or_msa: An ``ILexSense``, ``IMoInflAffMsa``, HVO, or
                ``MorphosyntaxAnalysis`` wrapper.

        Returns:
            list: ``IMoInflAffixSlot`` objects in ``SlotsRC`` order. An
            empty list when the sense has no MSA, the MSA is not
            inflectional-affix, or ``SlotsRC`` is empty.

        Raises:
            FP_NullParameterError: If ``sense_or_msa`` is null.

        Example:
            >>> slots = project.MSA.GetInflAffMsaSlots(sense)
            >>> hvos = {int(s.Hvo) for s in slots}
            >>> same = project.MSA.GetInflAffMsaSlots(infl_msa_hvo)
        """
        self._ValidateParam(sense_or_msa, "sense_or_msa")

        infl = self.__TryResolveInflAffMsa(sense_or_msa)
        if infl is None:
            return []

        slots_rc = infl.SlotsRC
        if slots_rc is None or slots_rc.Count == 0:
            return []
        return list(slots_rc)

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # MSA display-name + type discrimination (issue #575)
    # ------------------------------------------------------------------
    #
    # Scripts frequently read ``msa.LongName`` on the raw object (what FLEx
    # shows as the grammatical info, e.g. ``Verb  Pl.3``) and dispatch on
    # ``msa.ClassName`` to tell a stem MSA from an inflectional-affix,
    # derivational-affix or unclassified MSA. These two getters are the
    # public wrappers for both idioms.

    @OperationsMethod
    def GetLongName(self, msa_or_hvo):
        """
        Get the MSA's display summary (what FLEx shows as grammatical info).

        Reads the ``LongName`` LCM property on the resolved MSA -- e.g.
        ``"Verb  Pl.3"`` for a stem MSA -- normalizing FLEx's empty-string
        placeholder ``"***"`` to ``""`` (via
        ``BaseOperations._NormalizeMultiString``) so callers never have to
        compare against the raw placeholder.

        Args:
            msa_or_hvo: An MSA object, HVO, or GUID (resolved via the
                internal ``__GetMsaObject``).

        Returns:
            str: The MSA's ``LongName``; ``""`` when it is unset
            (``"***"``) or unreadable.

        Raises:
            FP_NullParameterError: If ``msa_or_hvo`` is null.

        Example:
            >>> msa = project.Senses.GetMSA(sense)
            >>> print(project.MSA.GetLongName(msa))
            Verb  Pl.3
            >>> print(repr(project.MSA.GetLongName(unset_msa)))
            ''

        See Also:
            GetMSAType, GetInflAffMsaSlots
        """
        self._ValidateParam(msa_or_hvo, "msa_or_hvo")

        msa = self.__GetMsaObject(msa_or_hvo)
        long_name = getattr(msa, "LongName", None)
        if not long_name:
            return ""
        return self._NormalizeMultiString(long_name)

    @OperationsMethod
    def GetMSAType(self, msa_or_hvo):
        """
        Classify an MSA as stem / inflectional / derivational / unclassified.

        Discriminates on the MSA's ``ClassName`` so scripts stop comparing
        ``ClassName`` strings directly (one of the most common raw-LCM
        idioms). The recognized mapping is:

        - ``MoStemMsa`` -> ``"stem"``
        - ``MoInflAffMsa`` -> ``"inflectional"``
        - ``MoDerivAffMsa`` -> ``"derivational"``
        - ``MoUnclassifiedAffixMsa`` -> ``"unclassified"``

        Args:
            msa_or_hvo: An MSA object, HVO, or GUID (resolved via the
                internal ``__GetMsaObject``).

        Returns:
            str: One of ``"stem"``, ``"inflectional"``, ``"derivational"``,
            ``"unclassified"``. For an unrecognized MSA subtype, falls
            back to the raw ``ClassName`` so no information is lost.

        Raises:
            FP_NullParameterError: If ``msa_or_hvo`` is null.

        Example:
            >>> msa = project.Senses.GetMSA(sense)
            >>> if project.MSA.GetMSAType(msa) == "stem":
            ...     print("stem MSA")
            stem MSA

        See Also:
            GetLongName, GetFeatures
        """
        self._ValidateParam(msa_or_hvo, "msa_or_hvo")

        msa = self.__GetMsaObject(msa_or_hvo)
        class_name = getattr(msa, "ClassName", None)
        return {
            "MoStemMsa": "stem",
            "MoInflAffMsa": "inflectional",
            "MoDerivAffMsa": "derivational",
            "MoUnclassifiedAffixMsa": "unclassified",
        }.get(class_name, class_name)

    # Stem-MSA inflection-class accessors (issue #573)
    # ------------------------------------------------------------------
    #
    # ``IMoStemMsa.InflectionClassRA`` had no public flexicon surface; the
    # only way to restore it after ``SetStemMsaPos`` was
    # ``IMoStemMsa(msa).InflectionClassRA = icl`` in raw LCM. These two
    # methods are the read/write pair. The write side validates that the
    # class belongs to the MSA's POS or its parent chain and raises
    # ``FP_ParameterError`` rather than silently attaching an incompatible
    # class. The POS parent-chain walk mirrors ``POSOperations.GetParent``'s
    # owner discrimination (``Owner`` with ``ClassName == "PartOfSpeech"``)
    # without round-tripping through the POS operations object.

    @OperationsMethod
    def GetInflectionClass(self, msa_or_hvo):
        """
        Read ``InflectionClassRA`` on a stem MSA.

        Args:
            msa_or_hvo: An MSA object, HVO, or GUID (resolved via the
                internal ``__GetMsaObject``).

        Returns:
            IMoInflClass | None: The stem MSA's inflection class, or
            ``None`` when it is unset or when the MSA is not a
            ``MoStemMsa`` (never raises on a wrong ClassName, matching
            this file's established never-raise idiom for type-gated
            reads).

        Raises:
            FP_NullParameterError: If ``msa_or_hvo`` is null.

        Example:
            >>> msa = project.Senses.GetMSA(sense)
            >>> icl = project.MSA.GetInflectionClass(msa)
            >>> print(icl.Name.BestAnalysisAlternative.Text if icl else "none")
            Regular Verb

        See Also:
            SetInflectionClass, SetStemMsaPos
        """
        self._ValidateParam(msa_or_hvo, "msa_or_hvo")

        msa = self.__GetMsaObject(msa_or_hvo)
        if getattr(msa, "ClassName", None) != "MoStemMsa":
            return None
        return getattr(msa, "InflectionClassRA", None)

    @OperationsMethod
    def SetInflectionClass(self, msa_or_hvo, infl_class_or_hvo_or_None):
        """
        Set (or clear) ``InflectionClassRA`` on a stem MSA.

        The class is validated before anything is mutated: it must belong
        to the MSA's part of speech or to one of its ancestor categories
        (walked upward via ``Owner``, mirroring
        ``POSOperations.GetParent``). A class from an unrelated POS raises
        ``FP_ParameterError`` with a clear message -- it is never silently
        attached.

        Args:
            msa_or_hvo: An MSA object, HVO, or GUID (resolved via the
                internal ``__GetMsaObject``).
            infl_class_or_hvo_or_None: An ``IMoInflClass`` object or its
                HVO, or ``None`` to clear the inflection class.

        Raises:
            FP_NullParameterError: If ``msa_or_hvo`` is null.
            FP_ParameterError: If the MSA is not a ``MoStemMsa``, if the
                inflection-class argument is not an ``IMoInflClass``, if
                the stem MSA has no part of speech to validate against, or
                if the class does not belong to the MSA's POS or its
                parent chain.
            FP_ReadOnlyError: If the project is not write-enabled.

        Example:
            >>> verb = project.POS.Find("Verb")
            >>> regular = next(c for c in project.POS.GetInflectionClasses(verb)
            ...                if "Regular" in c.Name.BestAnalysisAlternative.Text)
            >>> project.MSA.SetInflectionClass(msa, regular)
            >>> project.MSA.SetInflectionClass(msa, None)  # clear it

        See Also:
            GetInflectionClass, SetStemMsaPos
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(msa_or_hvo, "msa_or_hvo")

        msa = self.__GetMsaObject(msa_or_hvo)
        if getattr(msa, "ClassName", None) != "MoStemMsa":
            raise FP_ParameterError(
                "SetInflectionClass requires a stem MSA (MoStemMsa); "
                f"got ClassName {getattr(msa, 'ClassName', None)!r}."
            )

        # Resolution stays outside the bracket so an unresolvable or
        # invalid class raises before a named undo entry is opened (D5).
        target = self.__ResolveInflectionClass(infl_class_or_hvo_or_None)
        if target is not None:
            self.__ValidateInflectionClassForMsa(target, msa)

        with self._TransactionCM("Set stem MSA inflection class"):
            msa.InflectionClassRA = target

    def __ResolveInflectionClass(self, infl_class_or_hvo_or_None):
        """Resolve an inflection-class argument to an IMoInflClass or None.

        Accepts an object, HVO (int), or GUID (str). Casts to the concrete
        interface via ``cast_to_concrete`` because
        ``project.Object(hvo)`` returns a bare ``ICmObject``. Raises
        ``FP_ParameterError`` when the argument resolves to a non-MoInflClass
        object rather than silently accepting it.
        """
        if infl_class_or_hvo_or_None is None:
            return None
        if isinstance(infl_class_or_hvo_or_None, (int, str)):
            obj = self.project.Object(infl_class_or_hvo_or_None)
        else:
            obj = self._UnwrapLcm(infl_class_or_hvo_or_None)
        obj = cast_to_concrete(obj)
        if getattr(obj, "ClassName", None) != "MoInflClass":
            raise FP_ParameterError(
                "infl_class must be an IMoInflClass (or its HVO); "
                f"got ClassName {getattr(obj, 'ClassName', None)!r}."
            )
        return obj

    def __ValidateInflectionClassForMsa(self, infl_class, msa):
        """Raise FP_ParameterError unless the class fits the MSA's POS chain.

        A class "fits" when it appears in the ``InflectionClassesOC`` of
        the stem MSA's ``PartOfSpeechRA`` or of any ancestor category.
        """
        pos = getattr(msa, "PartOfSpeechRA", None)
        if pos is None:
            raise FP_ParameterError(
                "Cannot set an inflection class: the stem MSA has no part "
                "of speech, so the class cannot be validated against any "
                "POS. Set the POS first (e.g. via SetStemMsaPos)."
            )
        valid_hvos = self.__PosChainInflectionClassHvos(pos)
        if int(infl_class.Hvo) not in valid_hvos:
            pos_name = self.__PossibilityLabel(pos)
            class_name = self.__PossibilityLabel(infl_class)
            raise FP_ParameterError(
                f"Inflection class {class_name!r} does not belong to the "
                f"MSA's part of speech {pos_name!r} or any of its ancestor "
                "categories; refusing to attach an incompatible class."
            )

    def __PosChainInflectionClassHvos(self, pos):
        """HVOs of every inflection class on a POS and its ancestors.

        Walks upward via ``Owner`` discriminated by
        ``ClassName == "PartOfSpeech"`` (the same shape as
        ``POSOperations.GetParent``), collecting each category's
        ``InflectionClassesOC``. Guards against owner cycles.
        """
        hvos = set()
        seen = set()
        current = pos
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            for ic in getattr(current, "InflectionClassesOC", None) or ():
                hvos.add(int(ic.Hvo))
            owner = getattr(current, "Owner", None)
            current = (
                owner
                if getattr(owner, "ClassName", None) == "PartOfSpeech"
                else None
            )
        return hvos

    @staticmethod
    def __PossibilityLabel(obj):
        """Best-effort display label for an error message (never raises)."""
        try:
            return obj.Name.BestAnalysisAlternative.Text
        except Exception:
            pass
        try:
            return f"hvo={int(obj.Hvo)}"
        except Exception:
            return repr(obj)

    # ------------------------------------------------------------------
    # MSA exception features (issues #574, #630)
    # ------------------------------------------------------------------
    #
    # FLEx shows "Exception features" on stem, inflectional-affix and
    # derivational-affix MSAs (HermitCrab uses them to block rules and
    # affixes). In LCM the field differs per MSA type:
    #
    #   IMoStemMsa      -> ProdRestrictRC
    #   IMoInflAffMsa   -> FromProdRestrictRC
    #   IMoDerivAffMsa  -> FromProdRestrictRC and ToProdRestrictRC
    #   IMoUnclassifiedAffixMsa -> none
    #
    # Each is a reference collection of ICmPossibility items drawn from
    # MorphologicalDataOA.ProdRestrictOA (see
    # InflectionFeatureOperations.ExceptionFeatureGetAll / Find / Create).
    # They are NOT inflection classes.
    #
    # NOTE: this is a DIFFERENT field from
    # LexEntryOperations.GetRestrictions / LexSenseOperations.GetRestrictions
    # (the free-text Restrictions multistring), which is not a substitute.

    #: Valid values for the ``side`` keyword.
    _EXCEPTION_FEATURE_SIDES = ("from", "to")

    #: Human-readable list of the types that carry exception features.
    _EXCEPTION_FEATURE_TYPES_MSG = (
        "MoStemMsa (ProdRestrictRC), MoInflAffMsa (FromProdRestrictRC) "
        "and MoDerivAffMsa (FromProdRestrictRC / ToProdRestrictRC)"
    )

    def __ExceptionFeatureRC(self, msa, side="from"):
        """
        Return the exception-feature reference collection on ``msa`` for
        ``side``, cast to the concrete MSA interface.

        Mapping: ``MoStemMsa`` -> ``ProdRestrictRC`` (side ignored);
        ``MoInflAffMsa`` -> ``FromProdRestrictRC`` (``side="to"`` raises);
        ``MoDerivAffMsa`` -> ``FromProdRestrictRC`` / ``ToProdRestrictRC``.

        Raises:
            FP_ParameterError: ``side`` is not "from"/"to"; the MSA type
                carries no exception features; or ``side="to"`` on a
                ``MoInflAffMsa``.
        """
        if side not in self._EXCEPTION_FEATURE_SIDES:
            raise FP_ParameterError(
                f"side must be one of {list(self._EXCEPTION_FEATURE_SIDES)}; "
                f"got {side!r}"
            )
        class_name = getattr(msa, "ClassName", None)
        if class_name == "MoStemMsa":
            return IMoStemMsa(msa).ProdRestrictRC
        if class_name == "MoInflAffMsa":
            if side == "to":
                raise FP_ParameterError(
                    "MoInflAffMsa has only 'from' exception features "
                    "(FromProdRestrictRC); side='to' is not available. "
                    "Only MoDerivAffMsa has ToProdRestrictRC."
                )
            return IMoInflAffMsa(msa).FromProdRestrictRC
        if class_name == "MoDerivAffMsa":
            deriv = IMoDerivAffMsa(msa)
            if side == "to":
                return deriv.ToProdRestrictRC
            return deriv.FromProdRestrictRC
        raise FP_ParameterError(
            f"MSA type '{class_name}' does not carry exception features; "
            f"only {self._EXCEPTION_FEATURE_TYPES_MSG} do."
        )

    @staticmethod
    def __RCHasItems(msa, rc_name):
        """True when ``msa.<rc_name>`` is a non-empty reference collection."""
        rc = getattr(msa, rc_name, None)
        count = getattr(rc, "Count", 0)
        return isinstance(count, int) and count > 0

    def __ResolveExceptionFeature(self, feature_or_hvo):
        """
        Resolve an exception-feature parameter to ``ICmPossibility``.

        Accepts an ``ICmPossibility`` object (or a subclass instance),
        an HVO (int), or a GUID (str).

        Raises:
            FP_ParameterError: If the resolved object is not a
            ``CmPossibility``.
        """
        obj = self._UnwrapLcm(feature_or_hvo)
        if isinstance(obj, (int, str)):
            obj = self.project.Object(obj)
        try:
            return ICmPossibility(obj)
        except Exception:
            raise FP_ParameterError(
                "feature must be an ICmPossibility (or its HVO/GUID); "
                f"got {obj!r}"
            )

    @OperationsMethod
    def GetExceptionFeatures(self, msa_or_hvo, side="from"):
        """
        Get an MSA's exception features ("Exception features" in FLEx).

        Reads the per-type reference collection (HermitCrab uses these
        features to block rules/affixes):

        - ``MoStemMsa``: ``ProdRestrictRC`` (``side`` is ignored)
        - ``MoInflAffMsa``: ``FromProdRestrictRC`` (only ``side="from"``)
        - ``MoDerivAffMsa``: ``FromProdRestrictRC`` (``side="from"``) or
          ``ToProdRestrictRC`` (``side="to"``)

        The items are ``ICmPossibility`` entries from
        ``MorphologicalDataOA.ProdRestrictOA`` (see
        ``InflectionFeatureOperations.ExceptionFeatureGetAll``); they are
        not inflection classes.

        Args:
            msa_or_hvo: An MSA object, HVO, or GUID (resolved via the
                internal ``__GetMsaObject``).
            side: ``"from"`` (default) or ``"to"``. Only meaningful for
                ``MoDerivAffMsa``; ignored for ``MoStemMsa``.

        Returns:
            list[ICmPossibility]: The exception-feature possibility
            objects, so callers can read names/abbreviations via the
            existing possibility-list wrappers (e.g.
            ``PossibilityListOperations.GetItemName``). ``[]`` when none
            are set.

        Raises:
            FP_NullParameterError: If ``msa_or_hvo`` is null.
            FP_ParameterError: If ``side`` is not "from"/"to"; if the MSA
                type carries no exception features
                (``MoUnclassifiedAffixMsa``); or if ``side="to"`` is
                requested on a ``MoInflAffMsa``. (Changed in #630: an
                unsupported type now raises, consistent with
                ``AddExceptionFeature`` / ``RemoveExceptionFeature``,
                instead of silently returning ``[]``.)

        Example:
            >>> feats = project.MSA.GetExceptionFeatures(msa)
            >>> for feat in feats:
            ...     name = project.PossibilityLists.GetItemName(feat)
            ...     print(f"blocked unless: {name}")

            >>> # Derivational affix: the "to" side is a separate field
            >>> project.MSA.GetExceptionFeatures(deriv_msa, side="to")

        Notes:
            - This is NOT the same field as
              ``LexEntryOperations.GetRestrictions`` /
              ``LexSenseOperations.GetRestrictions`` (the free-text
              Restrictions multistring).

        See Also:
            AddExceptionFeature, RemoveExceptionFeature,
            InflectionFeatureOperations.ExceptionFeatureGetAll,
            PossibilityListOperations.GetItemName
        """
        self._ValidateParam(msa_or_hvo, "msa_or_hvo")

        msa = self.__GetMsaObject(msa_or_hvo)
        rc = self.__ExceptionFeatureRC(msa, side)
        return [ICmPossibility(item) for item in rc]

    @OperationsMethod
    def AddExceptionFeature(self, msa_or_hvo, feature_or_hvo, side="from"):
        """
        Add an exception feature to an MSA.

        Appends one ``ICmPossibility`` from
        ``MorphologicalDataOA.ProdRestrictOA`` to the MSA's exception
        features. The field written depends on the MSA type:

        - ``MoStemMsa``: ``ProdRestrictRC`` (``side`` is ignored)
        - ``MoInflAffMsa``: ``FromProdRestrictRC`` (only ``side="from"``)
        - ``MoDerivAffMsa``: ``FromProdRestrictRC`` (``side="from"``) or
          ``ToProdRestrictRC`` (``side="to"``)

        Args:
            msa_or_hvo: A stem, inflectional-affix, or
                derivational-affix MSA object, HVO, or GUID (resolved via
                the internal ``__GetMsaObject``).
            feature_or_hvo: An ``ICmPossibility`` object, HVO, or GUID.
            side: ``"from"`` (default) or ``"to"``; see above.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write
                enabled.
            FP_NullParameterError: If either parameter is null.
            FP_ParameterError: If ``side`` is not "from"/"to"; the MSA
                type carries no exception features
                (``MoUnclassifiedAffixMsa``); ``side="to"`` is requested
                on a ``MoInflAffMsa`` (it has no ``ToProdRestrictRC``);
                or the feature is not an ``ICmPossibility``.

        Example:
            >>> ef = project.InflectionFeatures.ExceptionFeatureFind("pl")
            >>> project.MSA.AddExceptionFeature(infl_msa, ef)
            >>> project.MSA.AddExceptionFeature(deriv_msa, ef, side="to")

        Notes:
            - Adding a feature that is already present is a no-op (no
              redundant undo entry): the membership test stays outside
              the transaction, mirroring ``RemovePhoneEnv``'s D5 idiom.
            - This is NOT the free-text Restrictions field -- see
              ``LexEntryOperations.GetRestrictions`` for that.

        See Also:
            GetExceptionFeatures, RemoveExceptionFeature,
            InflectionFeatureOperations.ExceptionFeatureCreate
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(msa_or_hvo, "msa_or_hvo")
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")

        msa = self.__GetMsaObject(msa_or_hvo)
        rc = self.__ExceptionFeatureRC(msa, side)
        poss = self.__ResolveExceptionFeature(feature_or_hvo)

        # Membership test stays outside the transaction so a redundant add
        # is a true no-op rather than an empty named undo entry (D5 --
        # same rationale as AllomorphOperations.RemovePhoneEnv).
        if poss not in rc:
            with self._TransactionCM("Add exception feature"):
                rc.Add(poss)

    @OperationsMethod
    def RemoveExceptionFeature(self, msa_or_hvo, feature_or_hvo, side="from"):
        """
        Remove an exception feature from an MSA.

        Removes one ``ICmPossibility`` from the MSA's exception features.
        The field touched depends on the MSA type:

        - ``MoStemMsa``: ``ProdRestrictRC`` (``side`` is ignored)
        - ``MoInflAffMsa``: ``FromProdRestrictRC`` (only ``side="from"``)
        - ``MoDerivAffMsa``: ``FromProdRestrictRC`` (``side="from"``) or
          ``ToProdRestrictRC`` (``side="to"``)

        Args:
            msa_or_hvo: A stem, inflectional-affix, or
                derivational-affix MSA object, HVO, or GUID (resolved via
                the internal ``__GetMsaObject``).
            feature_or_hvo: An ``ICmPossibility`` object, HVO, or GUID.
            side: ``"from"`` (default) or ``"to"``; see above.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write
                enabled.
            FP_NullParameterError: If either parameter is null.
            FP_ParameterError: If ``side`` is not "from"/"to"; the MSA
                type carries no exception features
                (``MoUnclassifiedAffixMsa``); ``side="to"`` is requested
                on a ``MoInflAffMsa``; or the feature is not an
                ``ICmPossibility``.

        Example:
            >>> feats = project.MSA.GetExceptionFeatures(msa)
            >>> if feats:
            ...     project.MSA.RemoveExceptionFeature(msa, feats[0])

        Notes:
            - If the feature is not present, this is a no-op (no error):
              the membership test stays outside the transaction so a
              redundant remove never opens an empty named undo entry
              (D5 -- same idiom as
              ``AllomorphOperations.RemovePhoneEnv``).

        See Also:
            GetExceptionFeatures, AddExceptionFeature
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(msa_or_hvo, "msa_or_hvo")
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")

        msa = self.__GetMsaObject(msa_or_hvo)
        rc = self.__ExceptionFeatureRC(msa, side)
        poss = self.__ResolveExceptionFeature(feature_or_hvo)

        # Membership test stays outside the bracket so a redundant remove
        # is a true no-op rather than an empty named undo entry (D5).
        if poss in rc:
            with self._TransactionCM("Remove exception feature"):
                rc.Remove(poss)

    # ------------------------------------------------------------------
    # MSA feature-structure getters (issue #544 -- reverse of MakeFeatStruc)
    # ------------------------------------------------------------------
    #
    # ``InflectionFeatures.MakeFeatStruc(specs, owner=msa, ...)`` writes an
    # MSA's feature structure, but until this section there was no public
    # way to read one back. The private ``__CaptureFeatureStrucProp`` (used
    # by ``GetSyncableProperties``) already resolves the owning property
    # and serializes via ``_GetFeatureStruc`` -- but that method returns the
    # C4 SYNC WIRE FORMAT (``{"TypeGuid": ..., "specs": {...}}``, nested
    # complex values carry an extra ``"Guid"`` key), which is NOT the shape
    # ``MakeFeatStruc`` accepts back (a plain recursive ``{feature: value |
    # {...}}`` dict). Confirmed by reading ``_MakeFeatStruc``/
    # ``__ResolveFeatStrucOperand`` directly: a GUID *string* resolves via
    # ``project.Object(guid)`` for either a feature or a value key, so a
    # dict of GUID-string keys/values is a valid, unambiguous
    # ``MakeFeatStruc`` input. ``__C4ToFeatStrucSpec`` performs that one
    # conversion (recursively, for nested ``IFsComplexValue`` structures),
    # so these getters return something that can be fed straight back into
    # ``MakeFeatStruc(getter_output, owner=other_msa)`` -- the round-trip
    # the issue asks for. NOTE: ``_MakeFeatStruc`` never sets ``TypeRA`` on
    # the struct it creates (only the C4/C5 sync-apply surface,
    # ``_ApplyFeatureStruc``, does), so ``TypeGuid`` carries no information
    # for a round trip through ``MakeFeatStruc`` and is intentionally
    # dropped by the converter -- this is a pre-existing ``MakeFeatStruc``
    # limitation, not something introduced here.

    def __C4ToFeatStrucSpec(self, c4):
        """
        Convert one ``_GetFeatureStruc`` (C4 wire-format) dict into the
        plain recursive dict ``_MakeFeatStruc`` accepts as ``specs``.

        Delegates to ``Shared.feature_struc_utils.c4_to_feat_struc_spec``
        -- the conversion is shared with
        ``AllomorphOperations.GetRequiredFeatures`` (issue #581) rather
        than duplicated. See that helper for the full contract
        (``None`` passthrough, ``{}`` for present-but-empty,
        ``TypeGuid`` and nested ``"Guid"`` keys dropped).

        Args:
            c4: A C4 dict (``{"TypeGuid": ..., "specs": {...}}``) as
                returned by ``_GetFeatureStruc``, or ``None``.

        Returns:
            dict or None: ``None`` when ``c4`` is ``None``; otherwise the
            ``MakeFeatStruc``-shaped spec.
        """
        return c4_to_feat_struc_spec(c4)

    def __ResolveMsaForFeatures(self, sense_or_msa):
        """
        Resolve ``sense_or_msa`` to a concrete, ``ClassName``-cast MSA
        object for the feature-structure getters, or ``None``.

        Accepts a sense (object/HVO/wrapper) -- reads its
        ``MorphoSyntaxAnalysisRA`` -- or an MSA (object/HVO/GUID/wrapper)
        directly, of ANY of the four concrete MSA classes (unlike
        ``__TryResolveInflAffMsa``, which only recognizes
        ``MoInflAffMsa``). Delegates the concrete cast to
        ``__GetMsaObject`` (C2) so every downstream getter receives a
        properly typed object regardless of entry path.

        Returns:
            The concrete MSA object, or ``None`` when ``sense_or_msa`` is
            a sense with no ``MorphoSyntaxAnalysisRA``.
        """
        obj = self.__Resolve(sense_or_msa)
        try:
            sense = ILexSense(obj)
        except Exception:
            sense = None

        if sense is not None:
            existing = sense.MorphoSyntaxAnalysisRA
            if existing is None:
                return None
            return self.__GetMsaObject(existing)

        return self.__GetMsaObject(obj)

    def __ReadMsaFeatureStrucSpec(self, msa, expected_class_name, slot):
        """
        Read one feature-struct owning property off ``msa`` and convert
        it to the ``_MakeFeatStruc``-shaped spec, or ``None``.

        Returns ``None`` (never raises) when ``msa.ClassName`` does not
        match ``expected_class_name`` -- mirrors ``GetInflAffMsaSlots``'s
        graceful non-raise on a wrong-type MSA, applied to this method's
        ``None``-shaped return instead of ``GetInflAffMsaSlots``'s ``[]``.
        """
        if msa.ClassName != expected_class_name:
            return None
        concrete_owner, prop_name = self._ResolveFeatureStrucOwner(
            msa, slot=slot
        )
        struct = getattr(concrete_owner, prop_name)
        return self.__C4ToFeatStrucSpec(self._GetFeatureStruc(struct))

    @OperationsMethod
    def GetStemFeatures(self, sense_or_msa):
        """
        Read ``IMoStemMsa.MsFeaturesOA`` as a ``MakeFeatStruc``-shaped spec.

        This is the read-side pair for
        ``project.InflectionFeatures.MakeFeatStruc(specs, owner=stem_msa)``:
        the returned spec can be fed straight back into ``MakeFeatStruc``
        to reproduce an equivalent (GUID-keyed) feature structure on
        another owner.

        Args:
            sense_or_msa: An ``ILexSense``, ``IMoStemMsa``, HVO, GUID
                string, or ``MorphosyntaxAnalysis`` wrapper.

        Returns:
            dict or None: Recursive ``{featureGuid: valueGuid | {...}}``
            spec. ``None`` when ``sense_or_msa`` denotes a sense with no
            MSA, an MSA that is not ``MoStemMsa``, or a stem MSA whose
            ``MsFeaturesOA`` is null. ``{}`` when ``MsFeaturesOA`` is a
            present-but-empty feature structure.

        Raises:
            FP_NullParameterError: If ``sense_or_msa`` is null.

        Example:
            >>> spec = project.MSA.GetStemFeatures(sense)
            >>> if spec is not None:
            ...     project.InflectionFeatures.MakeFeatStruc(
            ...         spec, owner=other_stem_msa
            ...     )
        """
        self._ValidateParam(sense_or_msa, "sense_or_msa")

        msa = self.__ResolveMsaForFeatures(sense_or_msa)
        if msa is None:
            return None
        return self.__ReadMsaFeatureStrucSpec(msa, "MoStemMsa", slot=None)

    @OperationsMethod
    def GetInflAffFeatures(self, sense_or_msa):
        """
        Read ``IMoInflAffMsa.InflFeatsOA`` as a ``MakeFeatStruc``-shaped
        spec.

        Read-side pair for
        ``project.InflectionFeatures.MakeFeatStruc(specs, owner=infl_msa)``.

        Args:
            sense_or_msa: An ``ILexSense``, ``IMoInflAffMsa``, HVO, GUID
                string, or ``MorphosyntaxAnalysis`` wrapper.

        Returns:
            dict or None: Recursive ``{featureGuid: valueGuid | {...}}``
            spec. ``None`` when ``sense_or_msa`` denotes a sense with no
            MSA, an MSA that is not ``MoInflAffMsa``, or an inflectional
            affix MSA whose ``InflFeatsOA`` is null. ``{}`` when
            ``InflFeatsOA`` is a present-but-empty feature structure.

        Raises:
            FP_NullParameterError: If ``sense_or_msa`` is null.

        Example:
            >>> spec = project.MSA.GetInflAffFeatures(sense)
            >>> if spec is not None:
            ...     project.InflectionFeatures.MakeFeatStruc(
            ...         spec, owner=other_infl_msa
            ...     )
        """
        self._ValidateParam(sense_or_msa, "sense_or_msa")

        msa = self.__ResolveMsaForFeatures(sense_or_msa)
        if msa is None:
            return None
        return self.__ReadMsaFeatureStrucSpec(msa, "MoInflAffMsa", slot=None)

    @OperationsMethod
    def GetDerivFromFeatures(self, sense_or_msa):
        """
        Read ``IMoDerivAffMsa.FromMsFeaturesOA`` as a ``MakeFeatStruc``-
        shaped spec.

        Read-side pair for
        ``project.InflectionFeatures.MakeFeatStruc(specs, owner=deriv_msa,
        slot="From")``.

        Args:
            sense_or_msa: An ``ILexSense``, ``IMoDerivAffMsa``, HVO, GUID
                string, or ``MorphosyntaxAnalysis`` wrapper.

        Returns:
            dict or None: Recursive ``{featureGuid: valueGuid | {...}}``
            spec. ``None`` when ``sense_or_msa`` denotes a sense with no
            MSA, an MSA that is not ``MoDerivAffMsa``, or a derivational
            affix MSA whose ``FromMsFeaturesOA`` is null. ``{}`` when
            ``FromMsFeaturesOA`` is a present-but-empty feature structure.

        Raises:
            FP_NullParameterError: If ``sense_or_msa`` is null.

        Example:
            >>> spec = project.MSA.GetDerivFromFeatures(sense)
            >>> if spec is not None:
            ...     project.InflectionFeatures.MakeFeatStruc(
            ...         spec, owner=other_deriv_msa, slot="From"
            ...     )
        """
        self._ValidateParam(sense_or_msa, "sense_or_msa")

        msa = self.__ResolveMsaForFeatures(sense_or_msa)
        if msa is None:
            return None
        return self.__ReadMsaFeatureStrucSpec(msa, "MoDerivAffMsa", slot="From")

    @OperationsMethod
    def GetDerivToFeatures(self, sense_or_msa):
        """
        Read ``IMoDerivAffMsa.ToMsFeaturesOA`` as a ``MakeFeatStruc``-
        shaped spec.

        Read-side pair for
        ``project.InflectionFeatures.MakeFeatStruc(specs, owner=deriv_msa,
        slot="To")``.

        Args:
            sense_or_msa: An ``ILexSense``, ``IMoDerivAffMsa``, HVO, GUID
                string, or ``MorphosyntaxAnalysis`` wrapper.

        Returns:
            dict or None: Recursive ``{featureGuid: valueGuid | {...}}``
            spec. ``None`` when ``sense_or_msa`` denotes a sense with no
            MSA, an MSA that is not ``MoDerivAffMsa``, or a derivational
            affix MSA whose ``ToMsFeaturesOA`` is null. ``{}`` when
            ``ToMsFeaturesOA`` is a present-but-empty feature structure.

        Raises:
            FP_NullParameterError: If ``sense_or_msa`` is null.

        Example:
            >>> spec = project.MSA.GetDerivToFeatures(sense)
            >>> if spec is not None:
            ...     project.InflectionFeatures.MakeFeatStruc(
            ...         spec, owner=other_deriv_msa, slot="To"
            ...     )
        """
        self._ValidateParam(sense_or_msa, "sense_or_msa")

        msa = self.__ResolveMsaForFeatures(sense_or_msa)
        if msa is None:
            return None
        return self.__ReadMsaFeatureStrucSpec(msa, "MoDerivAffMsa", slot="To")

    @OperationsMethod
    def GetFeatures(self, sense_or_msa, slot=None):
        """
        Read an MSA's feature structure as a ``MakeFeatStruc``-shaped
        spec, dispatching on the MSA's concrete ``ClassName``.

        Single entry point covering all four concrete MSA classes --
        prefer this over the explicit per-class getters
        (``GetStemFeatures`` / ``GetInflAffFeatures`` /
        ``GetDerivFromFeatures`` / ``GetDerivToFeatures``) when the
        caller does not already know the MSA's class (Principle III,
        docs/API_DESIGN_PHILOSOPHY.md).

        Args:
            sense_or_msa: An ``ILexSense``, any concrete MSA object, HVO,
                GUID string, or ``MorphosyntaxAnalysis`` wrapper.
            slot: Required ONLY for a ``MoDerivAffMsa`` (which has two
                independent feature-struct slots): ``"From"`` or ``"To"``.
                Ignored for every other MSA class, even if supplied.

        Returns:
            dict or None: Recursive ``{featureGuid: valueGuid | {...}}``
            spec (see the per-class getters for the exact owning
            property). ``None`` when ``sense_or_msa`` denotes a sense
            with no MSA, an ``MoUnclassifiedAffixMsa`` (carries no
            feature-struct property at all -- confirmed by the live
            probe backing ``GetSyncableProperties``), or any other
            ``ClassName`` outside the four recognized MSA subtypes.
            ``{}`` when the owning property is a present-but-empty
            feature structure.

        Raises:
            FP_NullParameterError: If ``sense_or_msa`` is null.
            FP_ParameterError: If the resolved MSA is ``MoDerivAffMsa``
                and ``slot`` is not ``"From"`` or ``"To"`` -- a
                derivational affix MSA has two independent feature-struct
                slots and this method never guesses which one the caller
                means.

        Example:
            >>> spec = project.MSA.GetFeatures(sense)
            >>> deriv_from = project.MSA.GetFeatures(deriv_msa, slot="From")
        """
        self._ValidateParam(sense_or_msa, "sense_or_msa")

        msa = self.__ResolveMsaForFeatures(sense_or_msa)
        if msa is None:
            return None

        class_name = msa.ClassName
        if class_name == "MoStemMsa":
            return self.__ReadMsaFeatureStrucSpec(msa, "MoStemMsa", slot=None)
        if class_name == "MoInflAffMsa":
            return self.__ReadMsaFeatureStrucSpec(msa, "MoInflAffMsa", slot=None)
        if class_name == "MoDerivAffMsa":
            if slot not in ("From", "To"):
                raise FP_ParameterError(
                    "GetFeatures: msa is MoDerivAffMsa, which has two "
                    "independent feature-struct slots; pass slot='From' "
                    "or slot='To'. Never guessed."
                )
            return self.__ReadMsaFeatureStrucSpec(msa, "MoDerivAffMsa", slot=slot)
        # MoUnclassifiedAffixMsa (R2: no feature-struct property at all)
        # and any out-of-C1-table ClassName (e.g. MoDerivStepMsa): no
        # feature-struct property to read.
        return None

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @OperationsMethod
    def GetOwningEntry(self, msa_or_hvo):
        """
        Get the lexical entry that owns this MSA.

        Same shape and semantics as
        ``AllomorphOperations.GetOwningEntry`` (issue #581): climbs the
        ownership chain via ``OwnerOfClass`` to the nearest ``ILexEntry``
        ancestor, rather than taking a single ``.Owner`` hop.

        Args:
            msa_or_hvo: An MSA object (``IMoStemMsa``,
                ``IMoInflAffMsa``, ``IMoDerivAffMsa`` or
                ``IMoUnclassifiedAffixMsa``), HVO, or GUID string.

        Returns:
            ILexEntry: The owning entry, or None if the MSA has no
            owning entry anywhere above it in the ownership chain.

        Raises:
            FP_NullParameterError: If msa_or_hvo is None.

        Example:
            >>> msa = project.MSA.GetAll(entry)[0]
            >>> owner = project.MSA.GetOwningEntry(msa)
            >>> print(project.LexEntry.GetHeadword(owner))
            run

            >>> # Accepts an HVO or GUID string as well
            >>> owner = project.MSA.GetOwningEntry(msa_hvo)

        Notes:
            - Returns None rather than raising when no owning entry
              exists. Callers must handle None; do not assume an entry
              is always found.
            - The null guard runs BEFORE the ILexEntry cast, because
              casting a null result is the crash this guard exists to
              prevent (same template as
              ``AllomorphOperations.GetOwningEntry``; the one-hop
              ``.Owner`` variants elsewhere are valid for their own
              owner shapes and are deliberately NOT the template here).

        See Also:
            GetAll, AllomorphOperations.GetOwningEntry
        """
        self._ValidateParam(msa_or_hvo, "msa_or_hvo")

        msa = self.__GetMsaObject(msa_or_hvo)

        # Template: AllomorphOperations.GetOwningEntry -- OwnerOfClass
        # walks Owner recursively and answers null when no ancestor of
        # the class is found (liblcm src/SIL.LCModel/DomainImpl/
        # CmObject.cs:3349).
        _owner = msa.OwnerOfClass(LexEntryTags.kClassId)
        if _owner is None:
            return None

        # Cast to the declared return type only after the null guard.
        # Raw OwnerOfClass output is typed ICmObject; pythonnet surfaces
        # ILexEntry members only after the explicit interface cast.
        return ILexEntry(_owner)

    # ------------------------------------------------------------------
    # Affix MSA variant conversion
    # ------------------------------------------------------------------

    # Map ClassName -> source kind tag for internal use.
    _AFFIX_CLASS_TO_KIND = {
        "MoInflAffMsa": "infl",
        "MoDerivAffMsa": "deriv",
        "MoUnclassifiedAffixMsa": "unclassified",
    }

    @OperationsMethod
    def ChangeAffixVariant(self, msa, target_kind: str):
        """
        Convert an existing affix MSA to a different affix variant.

        Creates a new MSA of the requested kind, copies the fields that
        transfer across the conversion, warns about fields that will be
        lost (only when they actually carry data), repoints all
        ILexSenses in the owning entry whose MorphoSyntaxAnalysisRA
        points at the old MSA, and removes the old MSA from
        MorphoSyntaxAnalysesOC when no senses remain referencing it.

        Args:
            msa: An existing affix MSA (IMoInflAffMsa, IMoDerivAffMsa,
                or IMoUnclassifiedAffixMsa), or a ``MorphosyntaxAnalysis``
                wrapper item from ``GetAll()`` (unwrapped internally,
                issue #449).
            target_kind: 'infl' | 'deriv' | 'unclassified'

        Returns:
            The new MSA (same type as requested by target_kind), or
            ``msa`` unchanged if source_kind == target_kind.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If msa is None.
            FP_ParameterError: If msa is not an affix MSA, or target_kind
                is not one of the recognised values.

        Notes:
            - WfiMorphBundle.MsaRA references are NOT scanned here, so an
              old MSA that is still referenced by morph bundles elsewhere
              in the project will be left in place even after all
              entry-local senses have been repointed. Call
              ``project.MSA.RemoveOrphaned(entry)`` (or
              ``RemoveOrphaned()`` for a project-wide sweep) afterwards
              to safely clean up any MSA that is truly unreferenced by
              both senses and morph bundles (issue #206).
            - Fields that cannot transfer across a conversion (SlotsRC,
              InflFeatsOA, FromPartOfSpeechRA, From/ToInflectionClassRA,
              StratumRA, From/ToProdRestrictRC) are logged as warnings
              only when they carry actual data on the source MSA.
        """
        self._EnsureWriteEnabled()
        msa = self._UnwrapLcm(msa)
        self._ValidateParam(msa, "msa")

        _VALID_KINDS = {"infl", "deriv", "unclassified"}
        if target_kind not in _VALID_KINDS:
            raise FP_ParameterError(
                f"target_kind must be one of {sorted(_VALID_KINDS)}; "
                f"got {target_kind!r}"
            )

        source_class = msa.ClassName
        source_kind = self._AFFIX_CLASS_TO_KIND.get(source_class)
        if source_kind is None:
            raise FP_ParameterError(
                f"msa must be an affix MSA (MoInflAffMsa, MoDerivAffMsa, "
                f"or MoUnclassifiedAffixMsa); got ClassName={source_class!r}"
            )

        if source_kind == target_kind:
            logger.debug(
                "ChangeAffixVariant: source and target kinds are both %r; "
                "returning msa unchanged.",
                target_kind,
            )
            return msa

        # Resolve the owning entry via the MSA's Owner.
        entry = ILexEntry(msa.Owner)

        # Build a temporary sense proxy to satisfy __CreateAndAttach's
        # interface: we need a sense that owns the entry so the factory
        # attaches the new MSA to the entry's MorphoSyntaxAnalysesOC.
        # We pick the first sense in the entry (they all share the same
        # owning entry; we will repoint senses manually after creation).
        senses_in_entry = list(entry.SensesOS)
        if not senses_in_entry:
            raise FP_ParameterError(
                "Owning entry has no senses; cannot attach a new MSA."
            )
        any_sense = senses_in_entry[0]

        # --- Determine the POS to carry into the new MSA ---
        # Conversion table for POS fields (spec table):
        #   Infl   -> Deriv:       PartOfSpeechRA      -> FromPartOfSpeechRA
        #   Infl   -> Unclass:     PartOfSpeechRA      -> PartOfSpeechRA
        #   Deriv  -> Infl:        ToPartOfSpeechRA    -> PartOfSpeechRA
        #   Deriv  -> Unclass:     ToPartOfSpeechRA    -> PartOfSpeechRA
        #   Unclass-> Infl:        PartOfSpeechRA      -> PartOfSpeechRA
        #   Unclass-> Deriv:       PartOfSpeechRA      -> ToPartOfSpeechRA
        if source_kind == "infl":
            concrete_src = IMoInflAffMsa(msa)
            src_pos = concrete_src.PartOfSpeechRA
        elif source_kind == "deriv":
            concrete_src = IMoDerivAffMsa(msa)
            src_pos = concrete_src.ToPartOfSpeechRA
        else:  # unclassified
            concrete_src = IMoUnclassifiedAffixMsa(msa)
            src_pos = concrete_src.PartOfSpeechRA

        # --- Warn about fields that will be lost (only if populated) ---
        lost_fields = []
        if source_kind == "infl" and target_kind in ("deriv", "unclassified"):
            infl_src = concrete_src
            if infl_src.SlotsRC is not None and infl_src.SlotsRC.Count > 0:
                lost_fields.append("SlotsRC")
            if infl_src.InflFeatsOA is not None:
                lost_fields.append("InflFeatsOA")
            if self.__RCHasItems(infl_src, "FromProdRestrictRC"):
                lost_fields.append("FromProdRestrictRC")
        elif source_kind == "deriv" and target_kind in ("infl", "unclassified"):
            deriv_src = concrete_src
            if deriv_src.FromPartOfSpeechRA is not None:
                lost_fields.append("FromPartOfSpeechRA")
            if (
                hasattr(deriv_src, "FromInflectionClassRA")
                and deriv_src.FromInflectionClassRA is not None
            ):
                lost_fields.append("FromInflectionClassRA")
            if (
                hasattr(deriv_src, "ToInflectionClassRA")
                and deriv_src.ToInflectionClassRA is not None
            ):
                lost_fields.append("ToInflectionClassRA")
            if (
                hasattr(deriv_src, "StratumRA")
                and deriv_src.StratumRA is not None
            ):
                lost_fields.append("StratumRA")
            for rc_name in ("FromProdRestrictRC", "ToProdRestrictRC"):
                if self.__RCHasItems(deriv_src, rc_name):
                    lost_fields.append(rc_name)

        if lost_fields:
            logger.warning(
                "ChangeAffixVariant: converting %r -> %r on entry Hvo=%s; "
                "the following fields carry data but cannot transfer to the "
                "new MSA variant and will be lost: %s",
                source_kind,
                target_kind,
                entry.Hvo,
                ", ".join(lost_fields),
            )

        # --- Create the new MSA ---
        # We temporarily attach it to any_sense; we will repoint senses
        # explicitly below, so this initial attachment is fine.
        sandbox = SandboxGenericMSA()
        if target_kind == "infl":
            sandbox.MsaType = MsaType.kInfl
            sandbox.MainPOS = src_pos
            raw_new = self.__CreateAndAttach(any_sense, sandbox, IMoInflAffMsaFactory)
            new_msa = IMoInflAffMsa(raw_new)
            # Unclass->Infl: PartOfSpeechRA is already set via MainPOS.
            # No additional field copies needed.
            # Deriv->Infl: ToPartOfSpeechRA -> PartOfSpeechRA (done via MainPOS).
        elif target_kind == "deriv":
            sandbox.MsaType = MsaType.kDeriv
            if source_kind == "infl":
                # Infl->Deriv: PartOfSpeechRA -> FromPartOfSpeechRA; ToPartOfSpeechRA is blank.
                sandbox.MainPOS = src_pos
                sandbox.SecondaryPOS = None
            else:
                # Unclass->Deriv: PartOfSpeechRA -> ToPartOfSpeechRA; FromPartOfSpeechRA is blank.
                sandbox.MainPOS = None
                sandbox.SecondaryPOS = src_pos
            raw_new = self.__CreateAndAttach(any_sense, sandbox, IMoDerivAffMsaFactory)
            new_msa = IMoDerivAffMsa(raw_new)
            # Patch the POS fields directly after creation since the
            # sandbox MainPOS/SecondaryPOS mapping may not be symmetric.
            # __CreateAndAttach's own bracket has already committed, so this
            # follow-up patch needs a transaction of its own (D6). The
            # source_kind dispatch stays INSIDE it: both branches mutate, so
            # there is no no-op path to protect (D5).
            with self._TransactionCM("Set derivational affix POS fields"):
                if source_kind == "infl":
                    new_msa.FromPartOfSpeechRA = src_pos
                    new_msa.ToPartOfSpeechRA = None
                else:
                    new_msa.ToPartOfSpeechRA = src_pos
                    new_msa.FromPartOfSpeechRA = None
        else:  # unclassified
            sandbox.MsaType = MsaType.kUnclassified
            sandbox.MainPOS = src_pos
            raw_new = self.__CreateAndAttach(any_sense, sandbox, IMoUnclassifiedAffixMsaFactory)
            new_msa = IMoUnclassifiedAffixMsa(raw_new)

        # --- Repoint all senses in the entry that reference the old MSA ---
        repointed = 0
        # The per-sense skip guards stay outside the bracket so a sense that
        # does not reference the old MSA is a true no-op rather than an empty
        # named undo entry (D5).
        for sense in entry.SensesOS:
            if sense.MorphoSyntaxAnalysisRA is not None:
                if sense.MorphoSyntaxAnalysisRA.Hvo == msa.Hvo:
                    with self._TransactionCM("Repoint sense to new MSA"):
                        sense.MorphoSyntaxAnalysisRA = new_msa
                    repointed += 1

        logger.debug(
            "ChangeAffixVariant: repointed %d sense(s) from old MSA Hvo=%s "
            "to new MSA Hvo=%s.",
            repointed,
            msa.Hvo,
            new_msa.Hvo,
        )

        # --- Detach old MSA if no senses reference it any longer ---
        # Check all senses in entry again after repointing.
        still_referenced = any(
            (s.MorphoSyntaxAnalysisRA is not None
             and s.MorphoSyntaxAnalysisRA.Hvo == msa.Hvo)
            for s in entry.SensesOS
        )
        if not still_referenced:
            # LCM may have already cascade-deleted the old MSA when
            # __CreateAndAttach overwrote the anchor sense's
            # MorphoSyntaxAnalysisRA, since a sense ref alone keeps the
            # MSA alive (cf. LT-14740 in OverridesLing_Lex.cs:1500).
            # Mirror LCM's own guard: only Remove() when still valid.
            if msa.IsValidObject:
                with self._TransactionCM("Remove superseded MSA"):
                    entry.MorphoSyntaxAnalysesOC.Remove(msa)
                logger.debug(
                    "ChangeAffixVariant: old MSA Hvo=%s removed from "
                    "MorphoSyntaxAnalysesOC (no senses remaining).",
                    msa.Hvo,
                )
            else:
                logger.debug(
                    "ChangeAffixVariant: old MSA was already cascade-"
                    "deleted by LCM; no explicit Remove needed."
                )
        else:
            logger.warning(
                "ChangeAffixVariant: old MSA Hvo=%s is still referenced by "
                "one or more senses after repointing and has been left in "
                "MorphoSyntaxAnalysesOC. Call RemoveOrphaned() afterwards "
                "to clean up any MSA that is truly unreferenced (issue #206).",
                msa.Hvo,
            )

        return new_msa

    # ------------------------------------------------------------------
    # Orphan cleanup
    # ------------------------------------------------------------------

    @OperationsMethod
    def RemoveOrphaned(self, entry=None, progress=None):
        """
        Remove MSAs that are no longer referenced by any sense or morph
        bundle.

        SetPartOfSpeech and ChangeAffixVariant detach a sense's
        MorphoSyntaxAnalysisRA from an old MSA when reassigning or
        converting it, but the old MSA can remain in its owning entry's
        MorphoSyntaxAnalysesOC. That is safe to leave in place ONLY if
        nothing else still points at it. This method performs the
        project-wide safety check and removes any MSA that is truly
        unreferenced.

        An MSA is considered orphaned iff it is referenced by NEITHER:
            1. Any ILexSense.MorphoSyntaxAnalysisRA (entry-local senses), NOR
            2. Any IWfiMorphBundle.MsaRA (project-wide, across all
               interlinear texts).

        Args:
            entry: An ILexEntry (or HVO) to limit the *scanned* MSAs to
                (only that entry's MorphoSyntaxAnalysesOC is examined for
                removal candidates). Pass None (the default) to sweep
                every entry in the project. In BOTH cases, the safety
                check against morph bundles is performed project-wide --
                scoping to a single entry never skips the bundle
                cross-check, since a bundle anywhere in the project can
                be the only thing keeping an entry-local MSA alive.
            progress: Optional callback invoked as ``progress(current,
                total)`` once per entry scanned, where ``total`` is the
                number of entries in scope (1 if ``entry`` was supplied,
                or the full entry count for a project-wide sweep). Pass
                None (the default) for no progress reporting. Exceptions
                raised by the callback are caught and logged, never
                propagated -- a broken progress reporter should not abort
                the sweep.

        Returns:
            RemoveOrphanedResult: namedtuple with ``removed_count``,
            ``kept_count``, ``removed`` (list[RemovedMSA]), and
            ``by_entry`` (list[EntryOrphanBreakdown]).

        Raises:
            FP_ReadOnlyError: If the project is not opened with write
                enabled.
            FP_ParameterError: If ``entry`` does not resolve to a valid
                ILexEntry.

        Notes:
            - Back-refs checked are exactly MorphoSyntaxAnalysisRA (on
              senses) and MsaRA (on morph bundles). LexemeFormOA /
              AlternateFormsOS allomorphs and ILexEntryRef do NOT carry
              MSA references and are intentionally not checked.
            - Performance: morph-bundle references are gathered in ONE
              pass over ``IWfiMorphBundleRepository.AllInstances()`` into
              a set of referenced HVOs, then each candidate MSA is tested
              against that set -- never an O(MSAs x bundles) nested scan.
            - Guards ``IsValidObject`` before removal, mirroring the
              cascade-delete guard already used by ChangeAffixVariant.
        """
        self._EnsureWriteEnabled()

        if entry is not None:
            entries = [self.__ResolveEntry(entry)]
        else:
            entries = list(self.project.ObjectsIn(ILexEntryRepository))

        # --- Project-wide morph-bundle reference set, built in ONE pass. ---
        # Safety-first (issue #206): even an entry-scoped call must
        # cross-check against ALL morph bundles project-wide, since a
        # bundle in some other interlinear text can be the only thing
        # keeping an otherwise entry-orphaned MSA alive.
        bundle_msa_hvos = set()
        for bundle in self.project.ObjectsIn(IWfiMorphBundleRepository):
            msa = bundle.MsaRA
            if msa is not None:
                bundle_msa_hvos.add(msa.Hvo)

        removed = []
        by_entry = []
        removed_count = 0
        kept_count = 0

        total = len(entries)
        with self._TransactionCM("Remove orphaned MSAs"):
            for i, entry_obj in enumerate(entries, start=1):
                # Entry-local sense back-refs.
                sense_msa_hvos = set()
                for sense in entry_obj.SensesOS:
                    msa_ra = sense.MorphoSyntaxAnalysisRA
                    if msa_ra is not None:
                        sense_msa_hvos.add(msa_ra.Hvo)

                entry_removed = 0
                entry_kept = 0

                # Snapshot the collection before mutating it -- removing
                # from MorphoSyntaxAnalysesOC while iterating it directly
                # would be unsafe.
                candidate_msas = list(entry_obj.MorphoSyntaxAnalysesOC)
                for msa in candidate_msas:
                    if msa.Hvo in sense_msa_hvos or msa.Hvo in bundle_msa_hvos:
                        entry_kept += 1
                        continue
                    if not msa.IsValidObject:
                        # Already gone (e.g. cascade-deleted); nothing to
                        # remove and nothing to count as kept.
                        continue
                    class_name = msa.ClassName
                    entry_obj.MorphoSyntaxAnalysesOC.Remove(msa)
                    removed.append(
                        RemovedMSA(entry_obj.Hvo, msa.Hvo, class_name)
                    )
                    entry_removed += 1

                removed_count += entry_removed
                kept_count += entry_kept
                if entry_removed or entry_kept:
                    by_entry.append(
                        EntryOrphanBreakdown(
                            entry_obj.Hvo, entry_removed, entry_kept
                        )
                    )

                if progress is not None:
                    try:
                        progress(i, total)
                    except Exception:
                        logger.debug(
                            "RemoveOrphaned: progress callback raised; "
                            "ignoring.",
                            exc_info=True,
                        )

        logger.info(
            "RemoveOrphaned: removed %d orphaned MSA(s), kept %d "
            "still-referenced MSA(s) across %d entr%s.",
            removed_count,
            kept_count,
            total,
            "y" if total == 1 else "ies",
        )

        return RemoveOrphanedResult(removed_count, kept_count, removed, by_entry)

    # ========== SYNC INTEGRATION METHODS ==========
    #
    # Closes issue #251 (spec feature-structure-sync-gap, task T6):
    # MSAOperations previously had ZERO sync methods, so every MSA synced
    # across projects carried a correct ClassName/POS but a permanently
    # null feature structure -- an MoStemMsa's MsFeaturesOA, an
    # MoInflAffMsa's InflFeatsOA, or an MoDerivAffMsa's From/ToMsFeaturesOA
    # (contract C1). Shape mirrors NaturalClassOperations'
    # GetSyncableProperties/ApplySyncableProperties (:1039/:1169), the
    # reference implementation for this whole feature family, but the
    # dispatch itself is unique to MSA: unlike a natural class (reached via
    # PhonologicalDataOA.NaturalClassesOS, always base-``IPhNaturalClass``-
    # typed), an MSA reached via ``entry.MorphoSyntaxAnalysesOC`` is
    # likewise base-``IMoMorphSynAnalysis``-typed, so ``hasattr`` on any of
    # ``MsFeaturesOA``/``InflFeatsOA``/``From``/``ToMsFeaturesOA`` is
    # 0/2088 True under pythonnet (spec D5, live probe) -- discriminating on
    # ``.ClassName`` (always visible on the base interface) and casting
    # explicitly via ``_ResolveFeatureStrucOwner`` (C1) is the only fix that
    # is not dead code.

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project
        synchronization of an MSA's feature structure(s).

        Args:
            item: An IMoStemMsa / IMoInflAffMsa / IMoDerivAffMsa /
                IMoUnclassifiedAffixMsa (or its HVO/GUID -- resolved and
                cast to the concrete interface via ``__GetMsaObject``,
                contract C2).

        Returns:
            dict: Keyed by ``ClassName`` (frozen C1 table rows for MSA):

            - ``MoStemMsa``: ``MsFeatures`` (C4 recursive-dict spec of
              ``MsFeaturesOA``) / ``MsFeaturesGuid`` (str GUID).
            - ``MoInflAffMsa``: ``InflFeats`` / ``InflFeatsGuid``
              (``InflFeatsOA``).
            - ``MoDerivAffMsa``: BOTH ``FromMsFeatures``/
              ``FromMsFeaturesGuid`` (``FromMsFeaturesOA``) AND
              ``ToMsFeatures``/``ToMsFeaturesGuid`` (``ToMsFeaturesOA``) --
              a derivational affix MSA has two independent feature-struct
              slots (C1 ``slot="From"``/``"To"``), each captured
              independently; either, both, or neither key-pair may be
              present depending on which slots are actually populated.
            - ``MoUnclassifiedAffixMsa``: always ``{}`` -- confirmed by the
              live probe to carry NO feature-struct property at all (R2).
              This ClassName is discriminated FIRST, before any resolver
              call, so capturing one of these (routinely created by
              ``CreateUnclassifiedAffix``) never raises.
            - Any other ``ClassName`` (e.g. ``MoDerivStepMsa`` -- out of
              the C1 table by design): always ``{}``. The resolver is
              never consulted for an out-of-table ClassName either, so
              this defensive fallback cannot raise -- mirrors
              ``NaturalClassOperations.GetSyncableProperties``'s own
              unknown-``ClassName`` fallback.

            An owning property that is present but genuinely empty (an
            ``IFsFeatStruc`` with zero ``FeatureSpecsOC`` entries) still
            emits BOTH its ``<Name>``/``<Name>Guid`` keys -- ``<Name>``
            serialises to ``{"TypeGuid": ..., "specs": {}}``, never
            ``None`` (C4). A NULL owning property (e.g. ``MsFeaturesOA``
            was never populated) omits both keys entirely -- gate on key
            PRESENCE (C6), never on the value's truthiness.

        Notes:
            - Emits ONLY the four C1 MSA rows -- no plain scalar or
              multistring MSA properties are captured here (POS
              references are T7's territory via ``POSOperations``, not
              this method's).
            - Zero ``hasattr`` gates on any feature-struct property:
              dispatch is entirely ``.ClassName``-driven, then delegates
              to ``BaseOperations._ResolveFeatureStrucOwner`` (cast) and
              ``_GetFeatureStruc`` (recursive C4 serialize).
        """
        msa = self.__GetMsaObject(item)
        props = {}
        class_name = msa.ClassName

        if class_name == "MoUnclassifiedAffixMsa":
            # R2 (lead ruling): MoUnclassifiedAffixMsa is EXCLUDED from
            # FEATURE_STRUC_OWNER_TABLE and the resolver raises on it BY
            # DESIGN -- but CreateUnclassifiedAffix (this very module)
            # manufactures these routinely, so capture meets them in
            # normal use. Discriminate here, BEFORE ever consulting the
            # resolver, so routine capture of an unclassified affix MSA
            # never raises. The live probe confirmed this ClassName
            # carries no feature-struct property at all.
            return props

        if class_name == "MoStemMsa":
            self.__CaptureFeatureStrucProp(props, msa, None, "MsFeatures")
        elif class_name == "MoInflAffMsa":
            self.__CaptureFeatureStrucProp(props, msa, None, "InflFeats")
        elif class_name == "MoDerivAffMsa":
            self.__CaptureFeatureStrucProp(props, msa, "From", "FromMsFeatures")
            self.__CaptureFeatureStrucProp(props, msa, "To", "ToMsFeatures")
        # else: ClassName outside the C1 table's four in-scope MSA rows
        # (e.g. MoDerivStepMsa, excluded by C1 -- never created by this
        # module). No feature-struct keys captured; the resolver is never
        # called here, so this defensive fallback cannot raise.

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """
        Apply syncable properties (from GetSyncableProperties) onto an MSA.

        Handles the four C1 MSA feature-struct key-pairs
        (``MsFeatures``/``MsFeaturesGuid``, ``InflFeats``/
        ``InflFeatsGuid``, ``FromMsFeatures``/``FromMsFeaturesGuid``,
        ``ToMsFeatures``/``ToMsFeaturesGuid``) directly; everything else in
        ``props`` (currently nothing, since ``GetSyncableProperties`` emits
        only these keys, but a caller-constructed ``props`` dict may carry
        more) is delegated to ``BaseOperations.ApplySyncableProperties``
        unchanged.

        Args:
            item: Target MSA (already created + owned + GUID-assigned by
                the caller), or its HVO/GUID (cast via ``__GetMsaObject``,
                C2).
            props: dict produced by GetSyncableProperties (or built by a
                caller following the same shape).
            ws_map: Optional source->target writing-system Id mapping.
                Unused by the feature-struct branches (which resolve by
                GUID, not writing system); passed through to the base
                loop for forward compatibility with any future plain
                scalar/multistring MSA property.
            fill_gaps: Passed through to the base loop. Has no additional
                effect on the feature-struct branches, which are always
                purely additive/idempotent by GUID (mirrors
                NaturalClassOperations' equivalent note).

        Raises:
            FP_ParameterError: If ``item`` is None, ``props`` is not a
                dict, or (C7) a ``<Name>``/``<Name>Guid`` spec references a
                feature, value, or feature-structure-type GUID that does
                not exist in the target project -- naming the unresolved
                GUID and instructing the caller to sync the feature system
                first. Silently dropping a spec would leave the target's
                MSA feature structure incomplete with no visible error
                (same bug class as the NaturalClassOperations/#222
                lineage).

        Notes:
            - The four feature-struct keys are POPPED out of ``props``
              (via a filtered copy) BEFORE calling ``super()`` (C6):
              ``BaseOperations._apply_props_loop`` dispatches on
              ``isinstance(value, dict)`` and would otherwise route a C4
              dict into the multi-writing-system multistring path and
              silently drop it.
            - Gates on KEY PRESENCE, never truthiness (C6): a present-but-
              empty feature structure (``<Name>Guid`` set, ``<Name>``
              absent/``{}``) is a real, empty-but-attached
              ``IFsFeatStruc`` on the source and must still create/attach
              an empty struct on the target, not be treated as "source has
              none".
            - ``MoUnclassifiedAffixMsa`` (R2) and any out-of-C1-table
              ClassName: no feature-struct branch runs; only the base
              loop's (here, empty) pass-through has any effect.
        """
        if item is None:
            raise FP_ParameterError("ApplySyncableProperties: item is None")
        if not isinstance(props, dict):
            raise FP_ParameterError(
                f"ApplySyncableProperties: props must be a dict, got "
                f"{type(props).__name__}"
            )

        msa = self.__GetMsaObject(item)
        class_name = msa.ClassName

        # Pop the four feature-struct key-pairs out of props BEFORE
        # calling super() (C6) -- BaseOperations._apply_props_loop
        # dispatches a dict value into the multistring path and would
        # drop a C4 dict silently at that layer instead of raising.
        base_props = {
            k: v for k, v in props.items() if k not in self.__FEATURE_STRUC_KEYS
        }
        super().ApplySyncableProperties(msa, base_props, ws_map, fill_gaps=fill_gaps)

        if class_name == "MoUnclassifiedAffixMsa":
            # R2: no feature-struct property on this ClassName; the
            # resolver is never consulted, so this cannot raise.
            return

        if class_name == "MoStemMsa":
            self.__ApplyFeatureStrucProp(msa, None, "MsFeatures", props)
        elif class_name == "MoInflAffMsa":
            self.__ApplyFeatureStrucProp(msa, None, "InflFeats", props)
        elif class_name == "MoDerivAffMsa":
            self.__ApplyFeatureStrucProp(msa, "From", "FromMsFeatures", props)
            self.__ApplyFeatureStrucProp(msa, "To", "ToMsFeatures", props)
        # else: ClassName outside the C1 table's four in-scope MSA rows --
        # nothing to apply; the resolver is never consulted here either.

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    # The eight props keys handled directly by ApplySyncableProperties'
    # feature-struct branches -- must be excluded from the base-loop
    # pass-through (C6). Kept as one tuple so the pop-filter and any
    # future audit share a single source of truth.
    __FEATURE_STRUC_KEYS = (
        "MsFeatures", "MsFeaturesGuid",
        "InflFeats", "InflFeatsGuid",
        "FromMsFeatures", "FromMsFeaturesGuid",
        "ToMsFeatures", "ToMsFeaturesGuid",
    )

    def __CaptureFeatureStrucProp(self, props, msa, slot, key):
        """
        Capture one C1 feature-struct row into ``props``, in place.

        Args:
            props: The dict being built by GetSyncableProperties;
                mutated in place.
            msa: The MSA object (any ClassName already confirmed by the
                caller to have a row in FEATURE_STRUC_OWNER_TABLE for
                this ``slot``).
            slot: ``None`` | ``"From"`` | ``"To"`` -- passed straight
                through to ``_ResolveFeatureStrucOwner`` (C1).
            key: The props key stem (e.g. ``"MsFeatures"``) -- the C1
                table's props-key column. ``f"{key}Guid"`` is the sibling
                GUID key.

        Notes:
            - Delegates the owner/property resolution entirely to
              ``BaseOperations._ResolveFeatureStrucOwner`` -- no
              ``hasattr`` probe, no local cast.
            - Only emits keys when the owning property is non-None (a
              present-but-empty struct still emits both keys, since
              ``_GetFeatureStruc`` never returns ``None`` for a non-None
              struct -- C4). A null owning property emits neither key,
              which is the PRESENCE gate C6 requires on the apply side.
        """
        concrete_owner, prop_name = self._ResolveFeatureStrucOwner(msa, slot=slot)
        struct = getattr(concrete_owner, prop_name)
        if struct is not None:
            props[key] = self._GetFeatureStruc(struct)
            props[f"{key}Guid"] = str(struct.Guid)

    def __ApplyFeatureStrucProp(self, msa, slot, key, props):
        """
        Apply one C1 feature-struct row from ``props`` onto ``msa``, if
        present.

        Args:
            msa: The MSA object (any ClassName already confirmed by the
                caller to have a row in FEATURE_STRUC_OWNER_TABLE for
                this ``slot``).
            slot: ``None`` | ``"From"`` | ``"To"`` -- passed straight
                through to ``_ResolveFeatureStrucOwner`` (C1).
            key: The props key stem (e.g. ``"MsFeatures"``).
            props: The ORIGINAL (unfiltered) props dict passed to
                ``ApplySyncableProperties`` -- read-only here.

        Notes:
            - Gates on KEY PRESENCE, never truthiness (C6):
              ``if key in props or guid_key in props`` -- a present-but-
              empty source struct carries ``<Name>Guid`` with ``<Name>``
              absent (or ``{}``), and must still create/attach an empty
              target struct, not be skipped as "source has none".
            - ``on_unresolved="raise"`` unconditionally (C7): an
              unresolvable feature/value/type GUID must never be
              silently dropped for an MSA sync -- a rule referencing an
              incomplete MSA would otherwise fail to match anything with
              no visible error (same policy as
              ``NaturalClassOperations.ApplySyncableProperties``).
        """
        guid_key = f"{key}Guid"
        if key in props or guid_key in props:
            concrete_owner, prop_name = self._ResolveFeatureStrucOwner(
                msa, slot=slot
            )
            spec = props.get(key) or {}
            struct_guid = props.get(guid_key)
            self._ApplyFeatureStruc(
                concrete_owner,
                prop_name,
                spec,
                struct_guid=struct_guid,
                on_unresolved="raise",
                label=f"MSA ({msa.ClassName}, {prop_name})",
            )

    def __GetMsaObject(self, msa_or_hvo):
        """
        Internal helper to resolve an MSA parameter to a concrete LCM
        object, accepting an object, HVO (int), or GUID (str).

        Casts to the concrete MSA interface -- ``IMoStemMsa`` /
        ``IMoInflAffMsa`` / ``IMoDerivAffMsa`` / ``IMoUnclassifiedAffixMsa``
        -- by ``ClassName`` BEFORE returning (contract C2).
        ``FLExProject.Object(hvo_or_guid)`` returns a bare ``ICmObject``;
        without this cast, a caller reaching ``GetSyncableProperties``/
        ``ApplySyncableProperties`` via an HVO or GUID string (rather than
        an already-typed object from, e.g., ``sense.MorphoSyntaxAnalysisRA``)
        would silently omit the feature-struct keys downstream wherever a
        subtype-only member were read directly -- this module avoids that
        specific failure mode by routing all subtype access through
        ``_ResolveFeatureStrucOwner`` (which casts internally regardless),
        so the eager cast here gives every downstream caller a properly
        concrete-typed object regardless of entry path.

        CORRECTION (2026-09-08, cycle 2 of spec
        260-environment-resolver-cast, task T5): this docstring previously
        claimed ``Grammar/NaturalClassOperations.py``'s
        ``__GetNaturalClassObject``/``__GetPhonemeObject`` were "sibling C2
        fix sites" implying they already cast the way this resolver does.
        They do NOT -- both are plain ``isinstance(x, int)`` HVO/object
        resolvers with no ``ClassName`` cast at all (confirmed by reading
        ``Grammar/NaturalClassOperations.py`` directly). That was a false
        "already fixed" marker; do not rely on it. Those two resolvers are
        part of the Class-A caller-usage re-triage tracked in
        ``specs/_archive/closed/260-environment-resolver-cast/STATUS.md`` and have not been
        fixed as of this correction.

        Args:
            msa_or_hvo: An MSA object, an ``LCMObjectWrapper``/
                ``PythonicWrapper`` wrapper (e.g. a ``MorphosyntaxAnalysis``
                item from ``GetAll()``, unwrapped via ``_UnwrapLcm``, issue
                #449), an HVO (``int``), or a GUID (``str``).

        Returns:
            The resolved MSA, cast to its concrete interface when its
            ``ClassName`` is one of the four recognised MSA subtypes.
            Any other ``ClassName`` (e.g. ``MoDerivStepMsa``) is returned
            unchanged -- ``.ClassName`` stays readable either way, and the
            dispatching callers above treat an unrecognised ClassName as
            a no-op, never a cast attempt.
        """
        msa_or_hvo = self._UnwrapLcm(msa_or_hvo)
        if isinstance(msa_or_hvo, (int, str)):
            obj = self.project.Object(msa_or_hvo)
        else:
            obj = msa_or_hvo

        class_name = getattr(obj, "ClassName", None)
        cast_iface = {
            "MoStemMsa": IMoStemMsa,
            "MoInflAffMsa": IMoInflAffMsa,
            "MoDerivAffMsa": IMoDerivAffMsa,
            "MoUnclassifiedAffixMsa": IMoUnclassifiedAffixMsa,
        }.get(class_name)
        if cast_iface is not None:
            return cast_iface(obj)
        return obj

    def __CreateAndAttach(self, sense, sandbox, factory_interface):
        """
        Common MSA-creation flow: resolve service, create with sandbox
        descriptor, attach to sense.

        Uses clr.GetClrType(factory_interface) because pythonnet's
        ServiceLocator.GetService overload needs the System.Type form of
        the interface rather than the raw interface object.
        """
        factory = self.project.project.ServiceLocator.GetService(
            clr.GetClrType(factory_interface)
        )
        if factory is None:
            raise FP_ParameterError(
                f"{factory_interface.__name__} service is unavailable."
            )

        # Factory.Create(owner, sandbox) -- the owner is the sense's
        # ENTRY, not the sense's direct Owner. For a subsense,
        # sense.Owner is the parent sense, not the entry; LCM expects
        # the enclosing ILexEntry, so walk up the ownership chain via
        # OwnerOfClass(LexEntryTags.kClassId). Same idiom that
        # LexSenseOperations.SetPartOfSpeech uses to resolve the owning
        # entry. (issue #129)
        entry = ILexEntry(sense.OwnerOfClass(LexEntryTags.kClassId))
        with self._TransactionCM("Create and attach MSA"):
            new_msa = factory.Create(entry, sandbox)
            sense.MorphoSyntaxAnalysisRA = new_msa
            return new_msa

    def __TryResolveInflAffMsa(self, sense_or_msa):
        """
        Return IMoInflAffMsa for sense_or_msa when it denotes one, else None.

        Accepts a sense (object/HVO/wrapper) or an inflectional-affix MSA
        directly. Non-inflectional MSAs and senses with no MSA yield None.
        """
        obj = self.__Resolve(sense_or_msa)
        try:
            sense = ILexSense(obj)
        except Exception:
            sense = None

        if sense is not None:
            existing = sense.MorphoSyntaxAnalysisRA
            if existing is None:
                return None
            try:
                return IMoInflAffMsa(existing)
            except Exception:
                return None

        try:
            return IMoInflAffMsa(obj)
        except Exception:
            return None

    def __ResolveSense(self, sense_or_hvo):
        """Resolve a sense parameter, accepting either an object or HVO."""
        if isinstance(sense_or_hvo, int):
            obj = self.project.Object(sense_or_hvo)
            return ILexSense(obj)
        # Pass through; assume the caller gave us a usable sense object
        # or wrapper. Wrappers' _obj is unwrapped lazily by LCM via the
        # operations they pass through to.
        if hasattr(sense_or_hvo, "_obj"):
            return sense_or_hvo._obj
        require_lcm_object(sense_or_hvo, "ILexSense")
        return sense_or_hvo

    def __Resolve(self, obj_or_hvo):
        """Generic resolve -- HVO -> object, wrapper -> unwrapped."""
        if isinstance(obj_or_hvo, int):
            return self.project.Object(obj_or_hvo)
        if hasattr(obj_or_hvo, "_obj"):
            return obj_or_hvo._obj
        require_lcm_object(obj_or_hvo, "an LCM")
        return obj_or_hvo

    def __ResolveEntry(self, entry_or_hvo):
        """Resolve an entry parameter, accepting either an object or HVO."""
        obj = self.__Resolve(entry_or_hvo)
        try:
            return ILexEntry(obj)
        except Exception:
            raise FP_ParameterError(
                "entry must be an ILexEntry (or its HVO); "
                f"got {obj!r}"
            )
