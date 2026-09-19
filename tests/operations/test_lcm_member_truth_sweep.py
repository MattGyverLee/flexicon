#
#   test_lcm_member_truth_sweep.py
#
#   Reflection + read-path ground-truth sweep for issues #259, #283,
#   #302, #261. Established live against SIL.LCModel via
#   clr.GetClrType (pure reflection, no project needed for Part 1/2a/3)
#   and, for #283(c)/(d), against a Sena 3 sandbox (tempdir copy,
#   nothing leaks into the real Sena 3).
#
#   This file makes NO production code change. It is read-path
#   reflection plus one authorized seeding write into sena3_sandbox
#   only, to settle a reference-vs-clone question about
#   IPhEnvironment.LeftContextRA/RightContextRA that the unmodified
#   Sena 3 fixture does not have data to answer.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def _dump_type_surface(iface, label):
    """Dump declared + inherited public properties and direct interfaces
    of a CLR interface type via clr.GetClrType. Returns the sorted list
    of property names for downstream assertions."""
    import clr

    net_type = clr.GetClrType(iface)
    props = sorted(p.Name for p in net_type.GetProperties())
    direct_interfaces = sorted(str(i) for i in net_type.GetInterfaces())

    lines = []
    lines.append("")
    lines.append("[SURFACE] " + label + " (" + str(iface) + ")")
    lines.append("[SURFACE] " + label + ": " + str(len(props)) + " public properties (declared+inherited):")
    for p in props:
        net_prop = net_type.GetProperty(p)
        lines.append("[SURFACE]   " + p + " : " + str(net_prop.PropertyType))
    lines.append("[SURFACE] " + label + ": direct .NET interfaces (" + str(len(direct_interfaces)) + "):")
    for i in direct_interfaces:
        lines.append("[SURFACE]   " + i)

    output = "\n".join(lines)
    print(output)
    return props, output


class TestPart1InflClassGroundTruth:
    """
    Pure clr.GetClrType reflection. No project needs to be open for this
    class assertions to be meaningful -- SIL.LCModel just needs to be
    importable, which the session fixture guarantees under
    -m requires_live_project.
    """

    def test_1a_wfimorphbundle_full_surface(self):
        pytest.importorskip("SIL.LCModel")
        from SIL.LCModel import IWfiMorphBundle

        props, _ = _dump_type_surface(IWfiMorphBundle, "IWfiMorphBundle")

        assert "InflClassRA" not in props, (
            "InflClassRA now exists on IWfiMorphBundle -- issue #259 "
            "premise (permanently-False hasattr guard) no longer holds; "
            "re-derive the verdict before citing this test."
        )

    def test_1b_msa_family_and_infltype_surfaces(self):
        pytest.importorskip("SIL.LCModel")
        import clr
        from SIL.LCModel import (
            IWfiMorphBundle,
            IMoStemMsa,
            IMoInflAffMsa,
            IMoMorphSynAnalysis,
            ILexEntryInflType,
        )

        net_type = clr.GetClrType(IWfiMorphBundle)
        msa_prop = net_type.GetProperty("MsaRA")
        infltype_prop = net_type.GetProperty("InflTypeRA")
        print("")
        print("[1b] IWfiMorphBundle.MsaRA declared CLR type: " + str(msa_prop.PropertyType if msa_prop else "NOT FOUND"))
        print("[1b] IWfiMorphBundle.InflTypeRA declared CLR type: " + str(infltype_prop.PropertyType if infltype_prop else "NOT FOUND"))

        assert msa_prop is not None, "MsaRA must exist on IWfiMorphBundle"
        assert infltype_prop is not None, "InflTypeRA must exist on IWfiMorphBundle"

        stem_props, _ = _dump_type_surface(IMoStemMsa, "IMoStemMsa")
        inflaff_props, _ = _dump_type_surface(IMoInflAffMsa, "IMoInflAffMsa")
        _dump_type_surface(IMoMorphSynAnalysis, "IMoMorphSynAnalysis (MsaRA base interface)")
        infltype_props, _ = _dump_type_surface(ILexEntryInflType, "ILexEntryInflType (InflTypeRA target)")

        infl_class_shaped_stem = [p for p in stem_props if "InflClass" in p]
        infl_class_shaped_inflaff = [p for p in inflaff_props if "InflClass" in p]
        print("")
        print("[1b] IMoStemMsa members containing InflClass: " + str(infl_class_shaped_stem))
        print("[1b] IMoInflAffMsa members containing InflClass: " + str(infl_class_shaped_inflaff))

        overlap = set(infltype_props) & {"InflClass", "InflClassRA"}
        print("[1b] ILexEntryInflType members overlapping an InflClass name: " + str(overlap))

    def test_1c_pos_inflection_classes_are_the_real_home(self):
        pytest.importorskip("SIL.LCModel")
        from SIL.LCModel import IPartOfSpeech, IMoStemMsa
        import clr

        pos_props, _ = _dump_type_surface(IPartOfSpeech, "IPartOfSpeech")
        assert "InflectionClassesOC" in pos_props

        stem_type = clr.GetClrType(IMoStemMsa)
        stem_props = {p.Name for p in stem_type.GetProperties()}
        infl_class_candidates = sorted(p for p in stem_props if "InflClass" in p)
        print("")
        print("[1c] IMoStemMsa properties containing InflClass: " + str(infl_class_candidates))
        for name in infl_class_candidates:
            prop = stem_type.GetProperty(name)
            print("[1c]   " + name + " : " + str(prop.PropertyType))


    @pytest.mark.live_phase("WfiMorphBundleOperations", "read")
    def test_1d_msa_navigation_safety_live_sena3(self, sena3_sandbox):
        """
        Part 1(d): confirm live whether navigating bundle.MsaRA ->
        InflectionClassRA is safe when MsaRA is null or resolves to an
        MSA subtype without an InflectionClassRA member (IMoInflAffMsa
        and the base IMoMorphSynAnalysis interface, per 1b/1c, do NOT
        declare it -- only IMoStemMsa does). Samples real morph bundles
        in the Sena 3 sandbox (read-only exploration; no writes).
        """
        from SIL.LCModel import (
            IWfiWordformRepository,
            IMoStemMsa,
        )
        from flexicon.code.lcm_casting import cast_to_concrete

        project = sena3_sandbox
        wordforms = list(project.ObjectsIn(IWfiWordformRepository))

        sampled = 0
        none_msa = 0
        class_name_counts = {}
        stem_with_class = 0
        stem_without_class = 0
        non_stem_attribute_error = 0

        for wf in wordforms:
            for analysis in wf.AnalysesOC:
                for bundle in analysis.MorphBundlesOS:
                    sampled += 1
                    msa_ra = bundle.MsaRA
                    if msa_ra is None:
                        none_msa += 1
                        continue

                    cn = msa_ra.ClassName
                    class_name_counts[cn] = class_name_counts.get(cn, 0) + 1

                    concrete = cast_to_concrete(msa_ra)
                    if isinstance(concrete, IMoStemMsa):
                        if concrete.InflectionClassRA is not None:
                            stem_with_class += 1
                        else:
                            stem_without_class += 1
                    else:
                        # Confirm the guard is load-bearing: a non-stem
                        # concrete MSA genuinely has no InflectionClassRA
                        # member -- direct Python attribute access raises,
                        # it does not silently return None.
                        try:
                            _ = concrete.InflectionClassRA
                        except AttributeError:
                            non_stem_attribute_error += 1

        print("")
        print("[1d] Sena 3 sandbox: sampled morph bundles: " + str(sampled))
        print("[1d] Sena 3 sandbox: bundles with MsaRA is None: " + str(none_msa))
        print("[1d] Sena 3 sandbox: MsaRA ClassName distribution: " + str(class_name_counts))
        print("[1d] Sena 3 sandbox: IMoStemMsa with InflectionClassRA set: " + str(stem_with_class))
        print("[1d] Sena 3 sandbox: IMoStemMsa with InflectionClassRA None: " + str(stem_without_class))
        print("[1d] Sena 3 sandbox: non-stem MSA raising AttributeError on .InflectionClassRA: " + str(non_stem_attribute_error))
        print(
            "[1d] CONCLUSION: MsaRA navigation to InflectionClassRA is safe "
            "ONLY behind (a) a None-check on MsaRA itself, AND (b) an "
            "isinstance/cast_to_concrete check narrowing to IMoStemMsa "
            "before touching InflectionClassRA -- a non-stem concrete MSA "
            "raises AttributeError rather than returning None, so a bare "
            "hasattr(bundle, \"InflClassRA\") style guard (permanently "
            "False today) must NOT be replaced with an equally-blind "
            "hasattr(msa, \"InflectionClassRA\") on an uncast object -- "
            "it must check concrete type first, exactly the cast-before-"
            "hasattr lesson already learned in #260/P7."
        )


class TestPart2EnvironmentContextGroundTruth:

    def test_2a_iphenvironment_full_surface(self):
        # Ground-truth reflection anchor, not a bug-asserting anchor --
        # NOT inverted under spec.md C7/C8's #283 fix (the LCM surface
        # itself never had LeftContextOA/RightContextOA; only production
        # code's property NAMES were wrong). See
        # specs/lcm-member-truth-sweep/spec.md C8(c).
        pytest.importorskip("SIL.LCModel")
        import clr
        from SIL.LCModel import IPhEnvironment

        props, _ = _dump_type_surface(IPhEnvironment, "IPhEnvironment")

        net_type = clr.GetClrType(IPhEnvironment)
        for name in ("LeftContextRA", "RightContextRA", "LeftContextOA", "RightContextOA"):
            prop = net_type.GetProperty(name)
            found = "FOUND, type=" + str(prop.PropertyType) if prop else "NOT FOUND"
            print("[2a] IPhEnvironment." + name + ": " + found)

        assert {"LeftContextRA", "RightContextRA"} <= set(props), (
            "expected real property names LeftContextRA/RightContextRA"
        )
        assert not ({"LeftContextOA", "RightContextOA"} & set(props)), (
            "LeftContextOA/RightContextOA now exist -- re-derive #283 premise"
        )

    @pytest.mark.live_phase("EnvironmentOperations", "read")
    def test_2c_sena3_prestate_context_population_count(self, sena3_sandbox):
        """
        Part 2(c): how many IPhEnvironment objects in Sena 3 have a
        non-null LeftContextRA / RightContextRA? This is the pre-state
        that justifies (or obviates) the 2(d) seeding.
        """
        project = sena3_sandbox
        phon_data = project.lp.PhonologicalDataOA
        envs = list(phon_data.EnvironmentsOS)

        n_left = sum(1 for e in envs if e.LeftContextRA is not None)
        n_right = sum(1 for e in envs if e.RightContextRA is not None)
        n_both = sum(
            1 for e in envs
            if e.LeftContextRA is not None and e.RightContextRA is not None
        )

        print("")
        print("[2c] Sena 3 sandbox: total IPhEnvironment objects: " + str(len(envs)))
        print("[2c] Sena 3 sandbox: non-null LeftContextRA: " + str(n_left))
        print("[2c] Sena 3 sandbox: non-null RightContextRA: " + str(n_right))
        print("[2c] Sena 3 sandbox: BOTH non-null (needed to settle #283): " + str(n_both))

    @pytest.mark.live_phase("EnvironmentOperations", "add")
    def test_2d_seed_and_observe_duplicate_reference_semantics(self, sena3_sandbox):
        """
        Part 2(d) -- EXPLICITLY AUTHORIZED SEEDING, sena3_sandbox ONLY.

        Builds a TEST_ environment with a genuine, populated
        LeftContextRA and RightContextRA (both IPhSimpleContextSeg
        wrapping a phoneme, the cheapest legal PhPhonContext subtype),
        duplicates it via project.Environments.Duplicate(), then
        RE-QUERIES both the source and duplicate from the LCM by HVO
        and compares LeftContextRA/RightContextRA identity (HVO) to
        determine reference vs. clone semantics.

        INVERTED under specs/lcm-member-truth-sweep/spec.md C7/C8 (#283):
        this originally only PRINTED its observation, because production
        Duplicate() wrote the nonexistent LeftContextOA/RightContextOA
        names and therefore dropped both contexts unconditionally. Now
        that Duplicate() copies LeftContextRA/RightContextRA by reference,
        this asserts the reference semantics as a hard requirement rather
        than merely observing them.
        """
        from SIL.LCModel import (
            IPhSimpleContextSegFactory,
            IPhPhonemeRepository,
            IPhEnvironment,
        )

        project = sena3_sandbox
        envs = project.Environments

        phonemes = list(project.ObjectsIn(IPhPhonemeRepository))
        assert phonemes, (
            "Sena 3 sandbox has no phonemes -- cannot build a legal "
            "PhSimpleContextSeg to seed a populated context; escalate, "
            "do not fabricate an illegal context object."
        )
        left_phoneme = phonemes[0]
        right_phoneme = phonemes[min(1, len(phonemes) - 1)]

        env = envs.Create(TEST_PREFIX + "283_seed_env")
        env_hvo = env.Hvo

        ctx_factory = project.project.ServiceLocator.GetService(IPhSimpleContextSegFactory)
        phon_data = project.lp.PhonologicalDataOA
        duplicate = None

        try:
            # envs is an Operations instance (EnvironmentOperations); use
            # its inherited _TransactionCM, the house pattern for writes,
            # rather than a manual BeginUndoTask/EndUndoTask pair -- the
            # sandbox session is opened undoable=False (a single
            # session-wide non-undoable task), so a second manual
            # BeginUndoTask nests illegally ("Nested tasks are not
            # supported"). _TransactionCM already accounts for this mode.
            #
            # IPhSimpleContextSeg is an OWNED object -- measured live
            # that assigning it directly to env.LeftContextRA before it
            # is owned anywhere raises LcmObjectUninitializedException.
            # It must first be added to the owning sequence
            # IPhPhonData.ContextsOS, THEN referenced by
            # LeftContextRA/RightContextRA. Its feature property is
            # FeatureStructureRA (not FeatureRA -- confirmed live via
            # clr.GetClrType(IPhSimpleContextSeg) in this same cycle).
            with envs._TransactionCM("TEST_283 seed context"):
                left_ctx = ctx_factory.Create()
                phon_data.ContextsOS.Add(left_ctx)
                left_ctx.FeatureStructureRA = left_phoneme
                env.LeftContextRA = left_ctx

                right_ctx = ctx_factory.Create()
                phon_data.ContextsOS.Add(right_ctx)
                right_ctx.FeatureStructureRA = right_phoneme
                env.RightContextRA = right_ctx

            # project.Object() returns a bare ICmObject view --
            # pythonnet's static wrapper-type gate means
            # LeftContextRA/RightContextRA are unreachable via
            # Python attribute access without an explicit cast
            # (measured live: AttributeError on the bare object).
            # Cast to IPhEnvironment, the same pattern
            # EnvironmentOperations.__ResolveObject uses internally.
            source_reread = IPhEnvironment(project.Object(env_hvo))
            src_left_hvo = source_reread.LeftContextRA.Hvo
            src_right_hvo = source_reread.RightContextRA.Hvo
            print("")
            print("[2d] source env hvo=" + str(env_hvo))
            print("[2d] source LeftContextRA hvo=" + str(src_left_hvo) + " ClassName=" + str(source_reread.LeftContextRA.ClassName))
            print("[2d] source RightContextRA hvo=" + str(src_right_hvo) + " ClassName=" + str(source_reread.RightContextRA.ClassName))

            duplicate = envs.Duplicate(source_reread, deep=True)
            dup_hvo = duplicate.Hvo

            dup_reread = IPhEnvironment(project.Object(dup_hvo))
            dup_left_ra = getattr(dup_reread, "LeftContextRA", None)
            dup_right_ra = getattr(dup_reread, "RightContextRA", None)
            dup_left_hvo = dup_left_ra.Hvo if dup_left_ra is not None else None
            dup_right_hvo = dup_right_ra.Hvo if dup_right_ra is not None else None
            print("[2d] duplicate env hvo=" + str(dup_hvo))
            print("[2d] duplicate LeftContextRA hvo=" + str(dup_left_hvo))
            print("[2d] duplicate RightContextRA hvo=" + str(dup_right_hvo))

            assert dup_left_hvo is not None, (
                "Duplicate() did not populate LeftContextRA on the copy -- "
                "expected reference-copy semantics per spec.md C7 (#283); "
                "re-derive if this regresses."
            )
            assert dup_right_hvo is not None, (
                "Duplicate() did not populate RightContextRA on the copy "
                "-- expected reference-copy semantics per spec.md C7 "
                "(#283); re-derive if this regresses."
            )
            assert dup_left_hvo == src_left_hvo, (
                "Duplicate's LeftContextRA HVO (" + str(dup_left_hvo) + ") "
                "does not match the source's (" + str(src_left_hvo) + ") -- "
                "expected the SAME IPhPhonContext object (reference "
                "semantics), not a clone."
            )
            assert dup_right_hvo == src_right_hvo, (
                "Duplicate's RightContextRA HVO (" + str(dup_right_hvo) + ") "
                "does not match the source's (" + str(src_right_hvo) + ") -- "
                "expected the SAME IPhPhonContext object (reference "
                "semantics), not a clone."
            )
            print("[2d] left same HVO (reference semantics): True")
            print("[2d] right same HVO (reference semantics): True")

        finally:
            # Best-effort cleanup. sena3_sandbox is a tempdir copy that
            # is discarded after the test regardless, so nothing leaks
            # into the real Sena 3 even if this cleanup is incomplete --
            # but restore discipline is followed anyway, including the
            # two seeded IPhPhonContext objects owned by
            # PhonologicalDataOA.ContextsOS (owned separately from the
            # environments that merely reference them).
            try:
                if duplicate is not None:
                    dup_left = getattr(duplicate, "LeftContextRA", None)
                    dup_right = getattr(duplicate, "RightContextRA", None)
                    with envs._TransactionCM("TEST_283 cleanup duplicate"):
                        if dup_left is not None and dup_left in phon_data.ContextsOS:
                            phon_data.ContextsOS.Remove(dup_left)
                        if dup_right is not None and dup_right in phon_data.ContextsOS:
                            phon_data.ContextsOS.Remove(dup_right)
                    envs.Delete(duplicate)
            except Exception:
                pass
            try:
                with envs._TransactionCM("TEST_283 cleanup seeded contexts"):
                    if left_ctx in phon_data.ContextsOS:
                        phon_data.ContextsOS.Remove(left_ctx)
                    if right_ctx in phon_data.ContextsOS:
                        phon_data.ContextsOS.Remove(right_ctx)
            except Exception:
                pass
            try:
                envs.Delete(env)
            except Exception:
                pass


class TestPart3NotebookRepositoryGroundTruth:

    def test_3a_rnresearchnbkrepository_surface(self):
        pytest.importorskip("SIL.LCModel")
        from SIL.LCModel import IRnResearchNbkRepository, IRnResearchNbk

        repo_props, _ = _dump_type_surface(IRnResearchNbkRepository, "IRnResearchNbkRepository")
        nbk_props, _ = _dump_type_surface(IRnResearchNbk, "IRnResearchNbk")

        print("")
        print("[3a] IRnResearchNbkRepository properties: " + str(repo_props))
        print("[3a] RecordsOC in IRnResearchNbkRepository: " + str("RecordsOC" in repo_props))
        print("[3a] Singleton in IRnResearchNbkRepository: " + str("Singleton" in repo_props))
        print("[3a] RecordsOC in IRnResearchNbk (the Singleton type): " + str("RecordsOC" in nbk_props))

    def test_3b_service_locator_precedent_for_hvo_to_icmobject(self):
        import inspect
        from flexicon.code.FLExProject import FLExProject
        from flexicon.code.Grammar.EnvironmentOperations import EnvironmentOperations

        object_src = inspect.getsource(FLExProject.Object)
        print("")
        print("[3b] FLExProject.Object source:")
        print(object_src)
        assert "ServiceLocator.GetObject" in object_src

        resolve_src = inspect.getsource(EnvironmentOperations)
        assert "self.project.Object(env_or_hvo)" in resolve_src, (
            "EnvironmentOperations __ResolveObject no longer routes "
            "through project.Object() -- re-derive the precedent"
        )
        print(
            "[3b] Precedent confirmed: "
            "flexicon/code/Grammar/EnvironmentOperations.py __ResolveObject "
            "calls self.project.Object(env_or_hvo), which is "
            "FLExProject.Object() -> self.project.ServiceLocator.GetObject(...) "
            "-- NOT the raw LcmCache.GetObject(hvo) that "
            "DataNotebookOperations.py:187 currently calls directly."
        )


class TestPart4NotebookOwnerGate:
    """
    T2.1 -- answers Q1, gates ruling C1 (spec.md section 3/4).

    C1 proposes rewriting #302's three DataNotebookOperations.py sites to
    the OWNERSHIP form (self.project.lp.ResearchNotebookOA.RecordsOC)
    rather than the REPOSITORY form (repos.Singleton.RecordsOC), on the
    premise that ResearchNotebookOA is never null where Singleton is not,
    and that the two resolve to the same underlying object. This class is
    READ-ONLY on both target_sandbox and sena3_sandbox -- no writes, no
    seeding, nothing to restore.
    """

    @pytest.mark.live_phase("DataNotebookOperations", "read")
    def test_4a_target_sandbox_ownership_vs_repository_gate(self, target_sandbox):
        self._probe(target_sandbox, "Target")

    @pytest.mark.live_phase("DataNotebookOperations", "read")
    def test_4b_sena3_sandbox_ownership_vs_repository_gate(self, sena3_sandbox):
        self._probe(sena3_sandbox, "Sena 3")

    @staticmethod
    def _probe(project, label):
        from SIL.LCModel import IRnResearchNbkRepository

        repo = project.project.ServiceLocator.GetService(IRnResearchNbkRepository)

        print("")
        print("[4] " + label + ": IRnResearchNbkRepository.Count = " + str(repo.Count))

        singleton = repo.Singleton
        singleton_is_null = singleton is None
        print("[4] " + label + ": repo.Singleton is None: " + str(singleton_is_null))

        owner = project.lp.ResearchNotebookOA
        owner_is_null = owner is None
        print("[4] " + label + ": project.lp.ResearchNotebookOA is None: " + str(owner_is_null))

        assert not owner_is_null, (
            "[4] " + label + ": project.lp.ResearchNotebookOA is NULL -- "
            "C1 (ownership form) FAILS this gate; ruling must flip to "
            "repos.Singleton.RecordsOC."
        )
        assert not singleton_is_null, (
            "[4] " + label + ": repo.Singleton is unexpectedly NULL -- "
            "re-derive Q1 before trusting either form."
        )

        print("[4] " + label + ": ResearchNotebookOA.Hvo = " + str(owner.Hvo))
        print("[4] " + label + ": repo.Singleton.Hvo = " + str(singleton.Hvo))
        assert owner.Hvo == singleton.Hvo, (
            "[4] " + label + ": ResearchNotebookOA.Hvo != repo.Singleton.Hvo "
            "-- they are NOT the same object; C1 FAILS this gate."
        )

        owner_records = list(owner.RecordsOC)
        singleton_records = list(singleton.RecordsOC)
        print("[4] " + label + ": ResearchNotebookOA.RecordsOC count = " + str(len(owner_records)))
        print("[4] " + label + ": repo.Singleton.RecordsOC count = " + str(len(singleton_records)))
        assert len(owner_records) == len(singleton_records), (
            "[4] " + label + ": RecordsOC counts differ between the "
            "ownership form and the repository form -- C1 FAILS this gate."
        )
        owner_hvos = sorted(r.Hvo for r in owner_records)
        singleton_hvos = sorted(r.Hvo for r in singleton_records)
        assert owner_hvos == singleton_hvos, (
            "[4] " + label + ": RecordsOC HVO sets differ between the "
            "ownership form and the repository form -- C1 FAILS this gate."
        )

        print(
            "[4] " + label + ": CONCLUSION: ResearchNotebookOA is non-null, "
            "HVO-identical to repos.Singleton, and RecordsOC agrees "
            "exactly (count + HVO set) between both access paths."
        )


class TestPart5CatalogueSiblingAbsenceRatchets:
    """
    T2.5 -- ruling C13 carve-out (spec.md section 3). Live-reflection
    ABSENCE ratchets for Catalogue 2 sibling rows (see
    specs/lcm-member-truth-sweep/catalogue2-siblings.md), upgrading them
    from "snapshot-derived, medium confidence" to "live-confirmed"
    before they are proposed as issues. Also pins ruling C2.

    NO production line for any of these rows is edited by this class --
    they are catalogued-only siblings, out of scope for behaviour
    change in this campaign. Pure clr.GetClrType reflection, exactly
    like TestPart1/TestPart2's (a) methods; no project needs to be
    open, only SIL.LCModel importable.
    """

    def test_5a_irngenericrec_has_no_textsrc(self):
        """
        Catalogue 2 rows 1-2 (Notebook/DataNotebookOperations.py
        LinkToText/UnlinkFromText, :1911,1913,1952,1954): both guard on
        record.TextsRC. IRnGenericRec carries TextRA (atomic reference)
        and no TextsRC at all.
        """
        pytest.importorskip("SIL.LCModel")
        from SIL.LCModel import IRnGenericRec

        props, _ = _dump_type_surface(IRnGenericRec, "IRnGenericRec")
        assert "TextRA" in props
        assert "TextsRC" not in props, (
            "TextsRC now exists on IRnGenericRec -- re-derive Catalogue 2 "
            "rows 1-2 before proposing them as issues"
        )

    def test_5b_icmanthroitem_has_no_textsrc(self):
        """
        Catalogue 2 rows 3-4 (Notebook/AnthropologyOperations.py
        AddText/RemoveText, :1403,1407,1461,1465): both guard on
        item.TextsRC. ICmAnthroItem has no TextsRC anywhere in its
        surface.
        """
        pytest.importorskip("SIL.LCModel")
        from SIL.LCModel import ICmAnthroItem

        props, _ = _dump_type_surface(ICmAnthroItem, "ICmAnthroItem")
        assert "TextsRC" not in props, (
            "TextsRC now exists on ICmAnthroItem -- re-derive Catalogue 2 "
            "rows 3-4 before proposing them as issues"
        )

    def test_5c_ilangproject_has_no_rectypesoa(self):
        """
        Carve-out row (Notebook/DataNotebookOperations.py:825,
        GetAllRecordTypes): guards on self.project.lp.RecTypesOA.
        ILangProject has no RecTypesOA.
        """
        pytest.importorskip("SIL.LCModel")
        from SIL.LCModel import ILangProject

        props, _ = _dump_type_surface(ILangProject, "ILangProject")
        assert "RecTypesOA" not in props, (
            "RecTypesOA now exists on ILangProject -- re-derive the "
            "carve-out row before proposing it as an issue"
        )

    def test_5d_icmperson_has_no_languagesrc(self):
        """
        Catalogue 2 row 5 (Notebook/PersonOperations.py:1067,
        Duplicate): guards on source.LanguagesRC. ICmPerson carries
        PositionsRC, PlacesOfResidenceRC, ResearchersRC, RestrictionsRC
        -- no LanguagesRC.
        """
        pytest.importorskip("SIL.LCModel")
        from SIL.LCModel import ICmPerson

        props, _ = _dump_type_surface(ICmPerson, "ICmPerson")
        assert "LanguagesRC" not in props, (
            "LanguagesRC now exists on ICmPerson -- re-derive Catalogue 2 "
            "row 5 before proposing it as an issue"
        )

    def test_5e_icmbaseannotation_has_no_repliesos(self):
        """
        Catalogue 2 rows 6-10 (Notebook/NoteOperations.py, multiple
        sites, and Notebook/annotation.py): all guard on some spelling
        of {,parent_,source_,owner.}RepliesOS against ICmBaseAnnotation.
        IScrScriptureNote uses ResponsesOS instead; ICmBaseAnnotation
        itself has no Replies* member.
        """
        pytest.importorskip("SIL.LCModel")
        from SIL.LCModel import ICmBaseAnnotation

        props, _ = _dump_type_surface(ICmBaseAnnotation, "ICmBaseAnnotation")
        assert "RepliesOS" not in props, (
            "RepliesOS now exists on ICmBaseAnnotation -- re-derive "
            "Catalogue 2 rows 6-10 before proposing them as issues"
        )

    def test_5f_pin_c2_rnresearchnbkrepository_surface(self):
        """
        Pins ruling C2 (spec.md section 3): IRnResearchNbkRepository
        exposes {Count, Singleton}. Live clr.GetClrType reflection on
        the INTERFACE itself (matching test_3a, cycle 1) shows only
        `Singleton` as a directly declared property -- `Count` is
        inherited from the generic base interface
        `IRepository<IRnResearchNbk>` and is not enumerated by
        `net_type.GetProperties()` on the derived interface (a CLR
        reflection-over-interfaces quirk, not evidence Count is
        missing). T2.1's own live evidence
        (evidence/live-T2.1-notebook-owner.md) already exercised
        `repo.Count` successfully (== 1) via runtime attribute access,
        so this test pins BOTH: the functional live access (hasattr +
        a real call, on the actual service, not just the interface
        type) AND the interface-level absence of RecordsOC.
        """
        pytest.importorskip("SIL.LCModel")
        from SIL.LCModel import IRnResearchNbkRepository

        props, _ = _dump_type_surface(
            IRnResearchNbkRepository, "IRnResearchNbkRepository"
        )
        assert "Singleton" in props
        assert "RecordsOC" not in props, (
            "RecordsOC now exists on IRnResearchNbkRepository -- "
            "re-derive ruling C1 (#302) before trusting this ratchet"
        )

    @pytest.mark.live_phase("DataNotebookOperations", "read")
    def test_5g_pin_c2_rnresearchnbkrepository_count_live(self, target_sandbox):
        """
        Functional half of the C2 pin: `repo.Count` and `repo.Singleton`
        both resolve at runtime on the real service (Count is inherited
        from the generic IRepository<T> base and does not show up via
        clr.GetClrType reflection on the derived interface -- see
        test_5f -- but it IS reachable live, exactly as T2.1 exercised).
        """
        from SIL.LCModel import IRnResearchNbkRepository

        repo = target_sandbox.project.ServiceLocator.GetService(
            IRnResearchNbkRepository
        )
        assert hasattr(repo, "Count")
        assert hasattr(repo, "Singleton")
        assert not hasattr(repo, "RecordsOC")
        assert isinstance(repo.Count, int)
        print("")
        print("[5g] live IRnResearchNbkRepository.Count = " + str(repo.Count))


class TestPart6CompoundContextSurfaceQ3:
    """
    T2.5b -- answers Q3 (spec.md section 4), Catalogue 2 row 25
    (Grammar/compound_rule.py:220,244). Ruling C9 (spec.md section 3)
    is binding: compound_rule.py is HANDS OFF in this campaign -- this
    class only records the live surface answer, it does not fix
    anything. A blind OA->RA rename there would be wrong in both
    directions if this comes back negative, and even a positive result
    (some suffix carries a context member) does not by itself justify
    an in-campaign fix; it only clears Catalogue 2 row 25 for separate
    filing.

    Live on target_sandbox: creates one real MoEndoCompound and one
    real MoExoCompound via the public
    project.MorphRules.CreateCompoundRule() API, then dumps BOTH the
    declared+inherited CLR property surface (clr.GetClrType, matching
    every other Part in this file) AND a live dir() over the actual
    instance, checking for any member whose name contains "Context"
    under any suffix (OA, RA, OS, RS, or bare).
    """

    @staticmethod
    def _context_named_members(props):
        return sorted(p for p in props if "Context" in p)

    @pytest.mark.live_phase("MorphRuleOperations", "add")
    def test_6a_moendocompound_and_moexocompound_context_surface(self, target_sandbox):
        from flexicon.code.lcm_casting import cast_to_concrete

        rules = target_sandbox.MorphRules
        endo = None
        exo = None
        try:
            endo = rules.CreateCompoundRule(
                f"{TEST_PREFIX}Q3_endo", endocentric=True
            )
            exo = rules.CreateCompoundRule(
                f"{TEST_PREFIX}Q3_exo", endocentric=False
            )

            assert endo.ClassName == "MoEndoCompound"
            assert exo.ClassName == "MoExoCompound"

            endo_concrete = cast_to_concrete(endo)
            exo_concrete = cast_to_concrete(exo)

            from SIL.LCModel import IMoEndoCompound, IMoExoCompound

            endo_props, _ = _dump_type_surface(IMoEndoCompound, "IMoEndoCompound")
            exo_props, _ = _dump_type_surface(IMoExoCompound, "IMoExoCompound")

            endo_context_props = self._context_named_members(endo_props)
            exo_context_props = self._context_named_members(exo_props)

            # Live dir() over the actual concrete instances -- catches
            # anything reflection-over-the-interface-type could miss
            # (e.g. a member added only on the runtime class, not the
            # declared interface).
            endo_dir_context = sorted(
                n for n in dir(endo_concrete) if "Context" in n
            )
            exo_dir_context = sorted(
                n for n in dir(exo_concrete) if "Context" in n
            )

            print("")
            print("[Q3] IMoEndoCompound CLR-reflection Context* members: " + str(endo_context_props))
            print("[Q3] IMoExoCompound CLR-reflection Context* members: " + str(exo_context_props))
            print("[Q3] live MoEndoCompound instance dir() Context* members: " + str(endo_dir_context))
            print("[Q3] live MoExoCompound instance dir() Context* members: " + str(exo_dir_context))

            any_context_member = bool(
                endo_context_props
                or exo_context_props
                or endo_dir_context
                or exo_dir_context
            )

            if any_context_member:
                print(
                    "[Q3] ANSWER: a Context-named member DOES exist under "
                    "one of these suffixes -- Catalogue 2 row 25 is "
                    "RAISED to HIGH confidence and should be filed as its "
                    "own issue (compound_rule.py stays hands-off in this "
                    "campaign per ruling C9)."
                )
            else:
                print(
                    "[Q3] ANSWER: no Context-named member exists under ANY "
                    "suffix (OA, RA, OS, RS, or bare) on either "
                    "MoEndoCompound or MoExoCompound -- Catalogue 2 row 25 "
                    "is CLEARED. left_context/right_context/contexts in "
                    "CompoundRule are unconditionally None for both "
                    "concrete types; there is no reference or owned "
                    "context to navigate to under any name. Confirms the "
                    "cycle-1 snapshot finding live."
                )

            # This class only records the answer (see class docstring);
            # it does not assert a particular outcome, since either
            # answer is informative and ruling C9 forbids acting on it
            # here either way.
        finally:
            for rule in (endo, exo):
                if rule is None:
                    continue
                try:
                    rules.Delete(rule)
                except Exception:
                    pass
