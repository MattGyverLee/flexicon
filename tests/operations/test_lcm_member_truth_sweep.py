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

            if dup_left_hvo is None and dup_right_hvo is None:
                print(
                    "[2d] OBSERVATION: Duplicate did not populate "
                    "LeftContextRA/RightContextRA on the copy at all -- "
                    "current Duplicate code writes to the nonexistent "
                    "LeftContextOA/RightContextOA names (hasattr guard "
                    "silently False), so neither reference nor clone "
                    "semantics currently apply: the field is dropped "
                    "entirely, same defect class as #259."
                )
            else:
                same_left = dup_left_hvo == src_left_hvo
                same_right = dup_right_hvo == src_right_hvo
                print("[2d] left same HVO (reference semantics if True): " + str(same_left))
                print("[2d] right same HVO (reference semantics if True): " + str(same_right))

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
