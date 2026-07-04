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

        from flexlibs2 import FLExProject

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
            pos: An IPartOfSpeech (or HVO) -- the grammatical category.

        Returns:
            IMoStemMsa: The newly created and attached MSA.

        Raises:
            FP_ReadOnlyError, FP_NullParameterError, FP_ParameterError.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(sense, "sense")
        self._ValidateParam(pos, "pos")

        sense_obj = self.__ResolveSense(sense)
        pos_obj = self.__Resolve(pos)

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
        deriv.ToPartOfSpeechRA = to_pos_obj
        return deriv

    @OperationsMethod
    def CreateInflAff(self, sense, pos, slots=None):
        """
        Create an IMoInflAffMsa, attach it to the sense.

        Args:
            sense: An ILexSense (or HVO) to attach the MSA to.
            pos: An IPartOfSpeech -- the category this affix inflects.
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
        self._ValidateParam(pos, "pos")

        sense_obj = self.__ResolveSense(sense)
        pos_obj = self.__Resolve(pos)

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
            pos: An IPartOfSpeech (or HVO) -- the grammatical category.

        Returns:
            IMoUnclassifiedAffixMsa: The newly created and attached MSA.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(sense, "sense")
        self._ValidateParam(pos, "pos")

        sense_obj = self.__ResolveSense(sense)
        pos_obj = self.__Resolve(pos)

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

        pos_obj = self.__Resolve(pos)
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
            - WfiMorphBundle.MsaRA references are NOT updated here; that
              is handled by a follow-up issue. An orphaned old MSA that
              is still referenced by morph bundles will be left in place
              and a warning is logged.
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
        for sense in entry.SensesOS:
            if sense.MorphoSyntaxAnalysisRA is not None:
                if sense.MorphoSyntaxAnalysisRA.Hvo == msa.Hvo:
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
                "MorphoSyntaxAnalysesOC. This is unexpected; a future "
                "orphan-cleanup API will address any residual references.",
                msa.Hvo,
            )

        return new_msa

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

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
