#
#   test_feature_struc_resolver.py
#
#   Coverage for BaseOperations._ResolveFeatureStrucOwner,
#   BaseOperations._GetFeatureStruc, and BaseOperations._ResolveFsByGuid --
#   spec feature-structure-sync-gap, Tasks T2 and T3.
#
#   Section A (no live LCM required): pure-Python branch coverage for the
#   resolver's raise paths that never touch SIL.LCModel (owner=None, no
#   ClassName, unknown/excluded ClassName, ambiguous-without-slot, wrong
#   slot) plus FEATURE_STRUC_OWNER_TABLE shape checks and the
#   struct-is-None short-circuit of _GetFeatureStruc.
#
#   Section B (requires_live_project, target_sandbox): every in-scope C1
#   ClassName resolved from a GUARANTEED bare ICmObject (discover .Hvo,
#   then re-fetch via project.Object(hvo) -- never assert against a
#   factory-fresh concrete object), slot-ignored-on-single-row, and the
#   MoUnclassifiedAffixMsa excluded-ClassName raise against a real live
#   instance.
#
#   Section C (requires_live_project, target_sandbox): a NESTED feature
#   structure built with RAW LCM factory calls (IFsFeatStrucFactory /
#   IFsComplexValueFactory / IFsClosedValueFactory), ownership-first at
#   every level -- deliberately NOT using MakeFeatStruc/T4/T5 helpers,
#   which would make this test circular -- re-read via a fresh
#   project.Object(hvo) fetch, and compared against the C4 dict shape.
#   Also the empty-but-present case, and _ResolveFsByGuid success/failure.
#
#   Section D (requires_live_project, sena3_sandbox): reports whether
#   Sena 3 contains any naturally nested MSA feature structure. Purely
#   informational -- does not assert either way.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest

from flexicon.code.BaseOperations import BaseOperations, FP_ParameterError
from flexicon.code.Shared.lcm_constants import FEATURE_STRUC_OWNER_TABLE


# ---------------------------------------------------------------------------
# Section A -- pure-Python branch coverage (no live LCM needed)
# ---------------------------------------------------------------------------


class _StubOwner:
    """Minimal stand-in exposing only `.ClassName` -- exercises the
    resolver's dict-lookup / slot-disambiguation branches, which return
    (raise) BEFORE any `SIL.LCModel` import happens. Used only for the
    branches that are pure Python logic; every branch that actually casts
    an object is covered live in Section B/C against real LCM instances.
    """

    def __init__(self, class_name):
        self.ClassName = class_name


@pytest.fixture
def ops():
    # BaseOperations._ResolveFeatureStrucOwner's raise branches never
    # touch self.project, so a bare instance (no real FLExProject) is
    # sufficient here.
    return BaseOperations(None)


class TestFeatureStrucOwnerTableShape:
    """FEATURE_STRUC_OWNER_TABLE is the single frozen C1 table -- pin its
    exact shape so a future edit to any row is a visible diff here."""

    def test_table_matches_frozen_c1(self):
        assert FEATURE_STRUC_OWNER_TABLE == {
            "MoStemMsa": ((None, "MsFeaturesOA", "MsFeatures"),),
            "MoInflAffMsa": ((None, "InflFeatsOA", "InflFeats"),),
            "MoDerivAffMsa": (
                ("From", "FromMsFeaturesOA", "FromMsFeatures"),
                ("To", "ToMsFeaturesOA", "ToMsFeatures"),
            ),
            "PartOfSpeech": (
                ("Default", "DefaultFeaturesOA", "DefaultFeatures"),
                ("InherFeatVal", "InherFeatValOA", "InherFeatVal"),
            ),
            "MoAffixAllomorph": ((None, "MsEnvFeaturesOA", "MsEnvFeatures"),),
            "PhNCFeatures": ((None, "FeaturesOA", "Features"),),
            "PhPhoneme": ((None, "FeaturesOA", "Features"),),
            "WfiAnalysis": ((None, "MsFeaturesOA", "MsFeatures"),),
        }

    def test_excluded_classnames_absent_from_table(self):
        # MoDerivStepMsa, LexEntryInflType, MoStemName,
        # MoUnclassifiedAffixMsa (confirmed live to carry NO feature-struct
        # property at all) and PosFeatures/FsComplexFeature (not resolver
        # rows -- see spec D2 note) must never appear as table keys.
        excluded = {
            "MoDerivStepMsa", "LexEntryInflType", "MoStemName",
            "MoUnclassifiedAffixMsa", "PosFeatures", "FsComplexFeature",
        }
        assert excluded.isdisjoint(FEATURE_STRUC_OWNER_TABLE)


class TestResolveFeatureStrucOwnerRaiseBranchesOffline(object):
    """Every raise branch that resolves BEFORE touching SIL.LCModel --
    exercised with plain owner=None / no-ClassName / stub objects. The
    branches that succeed (a real cast) are live-only (Section B)."""

    def test_owner_none_raises(self, ops):
        with pytest.raises(FP_ParameterError):
            ops._ResolveFeatureStrucOwner(None)

    def test_owner_without_classname_raises(self, ops):
        with pytest.raises(FP_ParameterError):
            ops._ResolveFeatureStrucOwner(object())

    @pytest.mark.parametrize(
        "class_name",
        [
            "MoDerivStepMsa",
            "LexEntryInflType",
            "MoStemName",
            "MoUnclassifiedAffixMsa",
            "SomeTotallyUnknownClassName",
        ],
    )
    def test_unknown_or_excluded_classname_raises_naming_it(self, ops, class_name):
        with pytest.raises(FP_ParameterError) as excinfo:
            ops._ResolveFeatureStrucOwner(_StubOwner(class_name))
        assert class_name in str(excinfo.value)

    def test_ambiguous_owner_without_slot_raises_naming_valid_slots(self, ops):
        with pytest.raises(FP_ParameterError) as excinfo:
            ops._ResolveFeatureStrucOwner(_StubOwner("MoDerivAffMsa"))
        msg = str(excinfo.value)
        assert "MoDerivAffMsa" in msg
        assert "From" in msg and "To" in msg

    def test_ambiguous_pos_without_slot_raises_naming_valid_slots(self, ops):
        with pytest.raises(FP_ParameterError) as excinfo:
            ops._ResolveFeatureStrucOwner(_StubOwner("PartOfSpeech"))
        msg = str(excinfo.value)
        assert "PartOfSpeech" in msg
        assert "Default" in msg and "InherFeatVal" in msg

    def test_ambiguous_owner_with_wrong_slot_raises(self, ops):
        with pytest.raises(FP_ParameterError) as excinfo:
            ops._ResolveFeatureStrucOwner(_StubOwner("MoDerivAffMsa"), slot="Bogus")
        assert "Bogus" in str(excinfo.value)


class TestGetFeatureStrucNoneShortCircuit:
    def test_none_struct_returns_none(self, ops):
        # struct is None is checked BEFORE any SIL.LCModel import, so this
        # is genuinely offline-safe.
        assert ops._GetFeatureStruc(None) is None


# ---------------------------------------------------------------------------
# Live fixtures (target_sandbox-backed)
# ---------------------------------------------------------------------------


@pytest.fixture
def feature_struc_family(target_sandbox):
    """
    Create one live instance of every in-scope C1 ClassName, plus the
    MoUnclassifiedAffixMsa excluded sibling, in a fresh target_sandbox.
    Yields a dict of HVOs (never live object references) so the test
    itself performs the mandated discover-.Hvo / re-fetch-via-
    project.Object(hvo) pattern.
    """
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")

    from SIL.LCModel import ILexSenseFactory

    sandbox = target_sandbox

    entry = sandbox.LexEntry.Create(lexeme_form="TEST_fsresolver")

    def _extra_sense():
        factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
        new_sense = factory.Create()
        entry.SensesOS.Add(new_sense)
        return new_sense

    existing_senses = list(entry.SensesOS)
    sense0 = existing_senses[0] if existing_senses else _extra_sense()
    sense1 = _extra_sense()
    sense2 = _extra_sense()
    sense3 = _extra_sense()

    pos_a = sandbox.POS.Create("TEST_fsresolver_posA", "tpA")
    pos_b = sandbox.POS.Create("TEST_fsresolver_posB", "tpB")

    stem = sandbox.MSA.CreateStem(sense0, pos_a)
    infl = sandbox.MSA.CreateInflAff(sense1, pos_a)
    deriv = sandbox.MSA.CreateDerivAff(sense2, pos_a, pos_b)
    unclassified = sandbox.MSA.CreateUnclassifiedAffix(sense3, pos_a)
    allomorph = sandbox.Allomorphs.Create(entry, "-TEST_suffix", morphType="suffix")

    nc = sandbox.NaturalClasses.CreateFeatureBased("TEST_fsresolver_nc")
    phoneme = sandbox.Phonemes.Create("TEST_fsresolver_p")

    wordform = sandbox.Wordforms.Create("TEST_fsresolver_wf")
    analysis = sandbox.WfiAnalyses.Create(wordform)

    hvos = {
        "MoStemMsa": stem.Hvo,
        "MoInflAffMsa": infl.Hvo,
        "MoDerivAffMsa": deriv.Hvo,
        "MoUnclassifiedAffixMsa": unclassified.Hvo,
        "MoAffixAllomorph": allomorph.Hvo,
        "PartOfSpeech": pos_a.Hvo,
        "PhNCFeatures": nc.Hvo,
        "PhPhoneme": phoneme.Hvo,
        "WfiAnalysis": analysis.Hvo,
        "_entry": entry.Hvo,
        "_pos_a": pos_a.Hvo,
        "_pos_b": pos_b.Hvo,
        "_nc": nc.Hvo,
        "_phoneme": phoneme.Hvo,
        "_wordform": wordform.Hvo,
    }

    yield sandbox, hvos

    # Cleanup, each independent so one failure doesn't block the rest.
    for label, action in (
        ("wordform (cascades analysis)", lambda: sandbox.Wordforms.Delete(hvos["_wordform"])),
        ("phoneme", lambda: sandbox.Phonemes.Delete(hvos["_phoneme"])),
        ("natural class", lambda: sandbox.NaturalClasses.Delete(hvos["_nc"])),
        ("entry (cascades MSAs/allomorph)", lambda: sandbox.LexEntry.Delete(hvos["_entry"])),
        ("POS A", lambda: sandbox.POS.Delete(hvos["_pos_a"])),
        ("POS B", lambda: sandbox.POS.Delete(hvos["_pos_b"])),
    ):
        try:
            action()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Section B -- T2 live coverage
# ---------------------------------------------------------------------------


@pytest.mark.requires_live_project
class TestResolveFeatureStrucOwnerLive:

    @pytest.mark.live_phase("BaseOperations", "read")
    @pytest.mark.parametrize(
        "class_name, slot, expected_prop",
        [
            ("MoStemMsa", None, "MsFeaturesOA"),
            ("MoInflAffMsa", None, "InflFeatsOA"),
            ("MoDerivAffMsa", "From", "FromMsFeaturesOA"),
            ("MoDerivAffMsa", "To", "ToMsFeaturesOA"),
            ("PartOfSpeech", "Default", "DefaultFeaturesOA"),
            ("PartOfSpeech", "InherFeatVal", "InherFeatValOA"),
            ("MoAffixAllomorph", None, "MsEnvFeaturesOA"),
            ("PhNCFeatures", None, "FeaturesOA"),
            ("PhPhoneme", None, "FeaturesOA"),
            ("WfiAnalysis", None, "MsFeaturesOA"),
        ],
    )
    def test_resolves_concrete_owner_and_prop_name(
        self, feature_struc_family, class_name, slot, expected_prop
    ):
        sandbox, hvos = feature_struc_family
        hvo = hvos[class_name]

        # Mandated pattern: discover .Hvo (done above at fixture-build
        # time), then re-fetch via project.Object(hvo) -- a guaranteed
        # bare ICmObject, never the factory-fresh concrete object.
        bare_obj = sandbox.Object(hvo)
        assert bare_obj.ClassName == class_name

        concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(
            bare_obj, slot=slot
        )
        assert prop_name == expected_prop
        assert concrete_owner.ClassName == class_name
        # The concrete cast must genuinely expose the resolved property --
        # this is the T1 regression the whole feature exists to close.
        assert hasattr(concrete_owner, prop_name), (
            f"{class_name}: cast result is missing {prop_name!r} -- "
            f"_interface_cache / _ResolveFeatureStrucOwner regression."
        )
        # Readback must not raise (may legitimately be None -- not
        # populated by this fixture).
        getattr(concrete_owner, prop_name)

    @pytest.mark.live_phase("BaseOperations", "read")
    def test_slot_ignored_on_single_row_owner_does_not_raise(
        self, feature_struc_family
    ):
        sandbox, hvos = feature_struc_family
        bare_obj = sandbox.Object(hvos["MoStemMsa"])

        # MoStemMsa has exactly one row -- an arbitrary slot= must be
        # silently ignored, not an error (frozen behaviour, C1 step 4).
        concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(
            bare_obj, slot="TotallyIrrelevant"
        )
        assert prop_name == "MsFeaturesOA"
        assert concrete_owner.ClassName == "MoStemMsa"

    @pytest.mark.live_phase("BaseOperations", "read")
    def test_excluded_classname_raises_against_real_live_instance(
        self, feature_struc_family
    ):
        sandbox, hvos = feature_struc_family
        bare_obj = sandbox.Object(hvos["MoUnclassifiedAffixMsa"])
        assert bare_obj.ClassName == "MoUnclassifiedAffixMsa"

        with pytest.raises(FP_ParameterError) as excinfo:
            sandbox.MSA._ResolveFeatureStrucOwner(bare_obj)
        assert "MoUnclassifiedAffixMsa" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Section C -- T3 live coverage
# ---------------------------------------------------------------------------


@pytest.mark.requires_live_project
class TestGetFeatureStrucLive:

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_nested_struct_round_trips_full_c4_shape(self, target_sandbox):
        from SIL.LCModel import (
            IFsFeatStrucFactory,
            IFsComplexValueFactory,
            IFsClosedValueFactory,
            IFsFeatStruc,
            IFsComplexValue,
            IFsClosedValue,
            ILexSenseFactory,
            IMoStemMsa,
        )

        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        entry = sandbox.LexEntry.Create(lexeme_form="TEST_fsnested")
        try:
            senses = list(entry.SensesOS)
            if not senses:
                factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
                new_sense = factory.Create()
                entry.SensesOS.Add(new_sense)
                senses = [new_sense]
            sense_obj = senses[0]

            pos_obj = sandbox.POS.Create("TEST_fsnested_pos", "tnp")
            stem = sandbox.MSA.CreateStem(sense_obj, pos_obj)

            # Real feature/value/complex-feature/type definitions -- a
            # nested spec's FeatureRA/ValueRA/ValueOA must resolve to
            # something real for the round trip to mean anything.
            closed_feat = infl_ops.Create("TEST_fsnested_feat", "tnf", type="closed")
            feat_value = infl_ops.CreateValue(closed_feat, "TEST_fsnested_val", "tnv")
            complex_feat = infl_ops.Create(
                "TEST_fsnested_complex", "tnc", type="complex"
            )
            inner_type = infl_ops.TypeCreate("TEST_fsnested_type", "tnty")

            fs_factory = sandbox.project.ServiceLocator.GetService(
                IFsFeatStrucFactory
            )
            cv_factory = sandbox.project.ServiceLocator.GetService(
                IFsComplexValueFactory
            )
            clv_factory = sandbox.project.ServiceLocator.GetService(
                IFsClosedValueFactory
            )

            # RAW LCM factory calls only -- deliberately NOT MakeFeatStruc
            # (that would be circular: T4/T5 haven't been built yet, and
            # even once they exist this test must stay independent of
            # them). Ownership-first at EVERY level.
            with sandbox._TransactionCM("T3 build nested feature structure"):
                top_struct = fs_factory.Create()
                stem.MsFeaturesOA = top_struct  # attach BEFORE populating
                top_struct = IFsFeatStruc(stem.MsFeaturesOA)
                # Outer TypeRA deliberately left NULL -- matches the live
                # shape (probe: only the outer TypeRA is null).

                raw_cv = cv_factory.Create()
                top_struct.FeatureSpecsOC.Add(raw_cv)  # attach before populating
                complex_value = IFsComplexValue(raw_cv)
                complex_value.FeatureRA = complex_feat

                nested_struct = fs_factory.Create()
                complex_value.ValueOA = nested_struct  # attach before populating
                nested_struct = IFsFeatStruc(complex_value.ValueOA)
                nested_struct.TypeRA = inner_type  # inner TypeRA non-null

                raw_clv = clv_factory.Create()
                nested_struct.FeatureSpecsOC.Add(raw_clv)  # attach before populating
                closed_value = IFsClosedValue(raw_clv)
                closed_value.FeatureRA = closed_feat
                closed_value.ValueRA = feat_value

            # Record write-time GUIDs as the expected values -- everything
            # asserted below is re-derived from a FRESH project.Object(hvo)
            # fetch, not from these live references.
            expected_complex_feat_guid = str(complex_feat.Guid)
            expected_closed_feat_guid = str(closed_feat.Guid)
            expected_feat_value_guid = str(feat_value.Guid)
            expected_inner_type_guid = str(inner_type.Guid)
            expected_nested_struct_guid = str(nested_struct.Guid)

            # Re-read from the LCM via a brand-new bare-object fetch.
            reread_bare = sandbox.Object(stem.Hvo)
            concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(
                reread_bare
            )
            assert prop_name == "MsFeaturesOA"
            reread_struct = getattr(concrete_owner, prop_name)

            result = sandbox.MSA._GetFeatureStruc(reread_struct)

            assert result["TypeGuid"] is None, (
                "Outer TypeRA must serialize as None -- it was never set."
            )
            assert "Guid" not in result, (
                "Top-level C4 dict must OMIT 'Guid' (only nested levels "
                "carry it)."
            )
            assert set(result["specs"].keys()) == {expected_complex_feat_guid}

            nested = result["specs"][expected_complex_feat_guid]
            assert nested["TypeGuid"] == expected_inner_type_guid, (
                "Per-level TypeGuid: inner TypeRA must be preserved even "
                "though the outer one is null."
            )
            assert nested["Guid"] == expected_nested_struct_guid, (
                "Nested levels must carry their own 'Guid'."
            )
            assert nested["specs"] == {
                expected_closed_feat_guid: expected_feat_value_guid
            }
        finally:
            sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("BaseOperations", "modify")
    def test_empty_but_present_struct_serializes_as_empty_specs_not_none(
        self, target_sandbox
    ):
        from SIL.LCModel import (
            IFsFeatStrucFactory,
            ILexSenseFactory,
            IMoInflAffMsa,
        )

        sandbox = target_sandbox

        entry = sandbox.LexEntry.Create(lexeme_form="TEST_fsempty")
        try:
            senses = list(entry.SensesOS)
            if not senses:
                factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
                new_sense = factory.Create()
                entry.SensesOS.Add(new_sense)
                senses = [new_sense]
            sense_obj = senses[0]

            pos_obj = sandbox.POS.Create("TEST_fsempty_pos", "tep")
            infl_msa = sandbox.MSA.CreateInflAff(sense_obj, pos_obj)

            fs_factory = sandbox.project.ServiceLocator.GetService(
                IFsFeatStrucFactory
            )
            with sandbox._TransactionCM("T3 attach empty feature structure"):
                empty_struct = fs_factory.Create()
                infl_msa.InflFeatsOA = empty_struct  # attach, never populated

            reread_bare = sandbox.Object(infl_msa.Hvo)
            concrete_owner, prop_name = sandbox.MSA._ResolveFeatureStrucOwner(
                reread_bare
            )
            assert prop_name == "InflFeatsOA"
            reread_struct = getattr(concrete_owner, prop_name)
            assert reread_struct is not None, (
                "Fixture bug: the struct must be present (attached, empty) "
                "for this test to mean anything -- a None struct here "
                "would trivially satisfy the wrong assertion."
            )

            result = sandbox.MSA._GetFeatureStruc(reread_struct)
            assert result == {"TypeGuid": None, "specs": {}}, (
                "An empty-but-present feature structure must serialize as "
                "{'TypeGuid': None, 'specs': {}} -- NEVER None. Only a "
                "genuinely null struct returns None."
            )
        finally:
            sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("BaseOperations", "read")
    def test_resolve_fs_by_guid_success_and_failure(self, target_sandbox):
        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        feat = infl_ops.Create("TEST_fsbyguid_feat", "tbg")
        try:
            found = sandbox.MSA._ResolveFsByGuid(str(feat.Guid), kind="feature")
            assert found is not None
            assert str(found.Guid) == str(feat.Guid)

            # A syntactically-plausible but nonexistent GUID must return
            # None, not raise -- the CALLER is responsible for raising
            # (contract C7).
            missing = sandbox.MSA._ResolveFsByGuid(
                "00000000-0000-0000-0000-000000000000", kind="feature"
            )
            assert missing is None

            # kind is diagnostic-only -- omitting it must behave identically.
            missing_no_kind = sandbox.MSA._ResolveFsByGuid(
                "00000000-0000-0000-0000-000000000000"
            )
            assert missing_no_kind is None
        finally:
            infl_ops.FeatureDelete(feat)


# ---------------------------------------------------------------------------
# Section D -- informational: does Sena 3 have naturally nested MSA
# feature structures?
# ---------------------------------------------------------------------------


@pytest.mark.requires_live_project
@pytest.mark.live_phase("BaseOperations", "read")
def test_sena3_natural_nesting_report(sena3_sandbox, capsys):
    """
    Purely informational: scans every MoStemMsa/MoInflAffMsa/MoDerivAffMsa
    in Sena 3 for a naturally-occurring nested (IFsComplexValue-bearing)
    feature structure, using BaseOperations._GetFeatureStruc itself so the
    report reflects exactly what T3's serializer produces. Does not assert
    either way -- the answer is recorded in the cycle-3 programmer report,
    not enforced here.
    """
    from SIL.LCModel import (
        ILexEntryRepository,
        IMoStemMsa,
        IMoInflAffMsa,
        IMoDerivAffMsa,
    )

    project = sena3_sandbox
    entries = list(project.ObjectsIn(ILexEntryRepository))

    def _has_nested(c4_dict):
        if not c4_dict:
            return False
        return any(isinstance(v, dict) for v in c4_dict.get("specs", {}).values())

    n_structs = 0
    n_nested = 0
    for entry in entries:
        for msa in entry.MorphoSyntaxAnalysesOC:
            cn = msa.ClassName
            structs = []
            if cn == "MoStemMsa":
                structs = [IMoStemMsa(msa).MsFeaturesOA]
            elif cn == "MoInflAffMsa":
                structs = [IMoInflAffMsa(msa).InflFeatsOA]
            elif cn == "MoDerivAffMsa":
                deriv = IMoDerivAffMsa(msa)
                structs = [deriv.FromMsFeaturesOA, deriv.ToMsFeaturesOA]
            for struct in structs:
                if struct is None:
                    continue
                n_structs += 1
                c4 = project.MSA._GetFeatureStruc(struct)
                if _has_nested(c4):
                    n_nested += 1

    print(
        f"\n[T3][Sena 3] non-null MSA feature structs: {n_structs}; "
        f"naturally nested (contains an IFsComplexValue spec): {n_nested}"
    )
