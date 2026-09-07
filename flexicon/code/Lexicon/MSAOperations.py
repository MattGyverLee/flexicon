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
from ..BaseOperations import BaseOperations, OperationsMethod

# Import FLEx LCM types
from SIL.LCModel import (
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
    Creation + attach operations for morphosyntactic analyses (MSAs).

    A LexSense's grammatical analysis lives in
    ``sense.MorphoSyntaxAnalysisRA``, which is a reference to an MSA owned
    by ``sense.Entry.MorphoSyntaxAnalysesOC``. LCM offers four concrete
    MSA subtypes that share IMoMorphSynAnalysis as base; each subtype has
    its own factory whose 2-arg Create overload takes an owner (the sense's
    entry) and a SandboxGenericMSA descriptor.

    This wrapper hides the ServiceLocator + SandboxGenericMSA dance and
    auto-attaches the new MSA to the sense, mirroring the read-side
    coverage in MorphosyntaxAnalysis.

    Usage::

        from flexicon import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        entry = list(project.LexiconAllEntries())[0]
        sense = entry.SensesOS[0]

        # Stem MSA (most common case): assign POS to a lexical entry.
        verb_pos = project.GramCat.Find("Verb")
        project.MSA.CreateStem(sense, verb_pos)

        # Derivational affix: noun -> verb
        n_pos = project.GramCat.Find("Noun")
        v_pos = project.GramCat.Find("Verb")
        project.MSA.CreateDerivAff(sense, from_pos=n_pos, to_pos=v_pos)

    See Also:
        morphosyntax_analysis.MorphosyntaxAnalysis (reading)
        msa_collection.MSACollection (iteration)
    """

    def __init__(self, project):
        super().__init__(project)

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
    def SetStemMsaPos(self, sense, pos):
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

        with self._TransactionCM("Set stem MSA POS"):
            stem.PartOfSpeechRA = pos_obj

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
                or IMoUnclassifiedAffixMsa).
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
        but the eager cast here still keeps this resolver symmetric with
        the sibling ``__GetNaturalClassObject``/``__GetPhonemeObject``
        C2 fix sites and gives every downstream caller a properly
        concrete-typed object regardless of entry path.

        Args:
            msa_or_hvo: An MSA object, a wrapper exposing one via
                ``._obj``, an HVO (``int``), or a GUID (``str``).

        Returns:
            The resolved MSA, cast to its concrete interface when its
            ``ClassName`` is one of the four recognised MSA subtypes.
            Any other ``ClassName`` (e.g. ``MoDerivStepMsa``) is returned
            unchanged -- ``.ClassName`` stays readable either way, and the
            dispatching callers above treat an unrecognised ClassName as
            a no-op, never a cast attempt.
        """
        if isinstance(msa_or_hvo, (int, str)):
            obj = self.project.Object(msa_or_hvo)
        elif hasattr(msa_or_hvo, "_obj"):
            obj = msa_or_hvo._obj
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
        return sense_or_hvo

    def __Resolve(self, obj_or_hvo):
        """Generic resolve -- HVO -> object, wrapper -> unwrapped."""
        if isinstance(obj_or_hvo, int):
            return self.project.Object(obj_or_hvo)
        if hasattr(obj_or_hvo, "_obj"):
            return obj_or_hvo._obj
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
