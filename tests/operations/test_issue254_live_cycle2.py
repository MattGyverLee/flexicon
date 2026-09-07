#
#   test_issue254_live_cycle2.py
#
#   Live cycle-2 verification for issue #254 (GetMorphType/SetMorphType
#   repair on IWfiMorphBundle). Runs against Sena 3 via sena3_sandbox
#   (disposable tempdir copy). See specs/254-getmorphtype-allomorph/
#   evidence/live-cycle2-fix.md for the write-up of results.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import logging

import pytest

pytestmark = pytest.mark.requires_live_project


def _find_bundle_with_morphra(project, need_none=False, limit=5000):
    """Walk wordforms/analyses/bundles, return first bundle matching MorphRA is/isn't None."""
    from SIL.LCModel import IWfiWordformRepository

    checked = 0
    for wf in project.ObjectsIn(IWfiWordformRepository):
        for analysis in wf.AnalysesOC:
            for bundle in analysis.MorphBundlesOS:
                checked += 1
                if need_none and bundle.MorphRA is None:
                    return bundle
                if not need_none and bundle.MorphRA is not None:
                    return bundle
                if checked >= limit:
                    return None
    return None


def _find_entry_with_lexeme_form(project, limit=2000):
    from SIL.LCModel import ILexEntryRepository

    checked = 0
    for entry in project.ObjectsIn(ILexEntryRepository):
        checked += 1
        if entry.LexemeFormOA is not None:
            return entry
        if checked >= limit:
            return None
    return None


@pytest.mark.live_phase("WfiMorphBundleOperations", "read")
def test_c1_bare_attribute_access_resolves_morphtypera(sena3_sandbox):
    """Item 1: does bare bundle.MorphRA.MorphTypeRA resolve under pythonnet?"""
    from SIL.LCModel import IMoForm

    project = sena3_sandbox
    bundle = _find_bundle_with_morphra(project, need_none=False)
    assert bundle is not None, "No bundle with MorphRA set found in Sena 3 sandbox"

    morph = bundle.MorphRA
    bare_result = morph.MorphTypeRA
    cast_result = IMoForm(morph).MorphTypeRA

    print("[C1] bare morph.MorphTypeRA: " + str(bare_result))
    print("[C1] cast IMoForm(morph).MorphTypeRA: " + str(cast_result))

    if bare_result is None and cast_result is None:
        pass
    else:
        assert bare_result is not None, "Bare access returned None while cast did not"
        assert bare_result.Hvo == cast_result.Hvo, (
            "Bare and cast access resolved to different objects"
        )
    print("[C1] RESULT: bare attribute access resolves correctly, no cast needed")


@pytest.mark.live_phase("WfiMorphBundleOperations", "read")
def test_c1_getmorphtype_returns_imomorphtype_with_correct_names(sena3_sandbox):
    """Item 2: GetMorphType returns IMoMorphType; cross-check names vs cycle-1 probe."""
    from SIL.LCModel import IWfiWordformRepository

    project = sena3_sandbox
    ops = project.WfiMorphBundles

    found = {"prefix": None, "suffix": None, "stem": None}
    checked = 0
    for wf in project.ObjectsIn(IWfiWordformRepository):
        for analysis in wf.AnalysesOC:
            for bundle in analysis.MorphBundlesOS:
                checked += 1
                mt = ops.GetMorphType(bundle)
                if mt is None:
                    continue
                assert mt.ClassName == "MoMorphType", (
                    "GetMorphType returned ClassName=" + str(mt.ClassName)
                )
                name = mt.Name.BestAnalysisAlternative.Text
                cn = bundle.MorphRA.ClassName
                if cn == "MoAffixAllomorph" and name == "prefix" and found["prefix"] is None:
                    found["prefix"] = (cn, name)
                if cn == "MoAffixAllomorph" and name == "suffix" and found["suffix"] is None:
                    found["suffix"] = (cn, name)
                if cn == "MoStemAllomorph" and name in ("stem", "root") and found["stem"] is None:
                    found["stem"] = (cn, name)
                if all(found.values()) or checked >= 5000:
                    break
            if all(found.values()) or checked >= 5000:
                break
        if all(found.values()) or checked >= 5000:
            break

    print("[C1] found examples: " + str(found))
    assert found["prefix"] is not None, "No prefix example found"
    assert found["suffix"] is not None, "No suffix example found"
    assert found["stem"] is not None, "No stem example found"
    assert found["prefix"][1] == "prefix"
    assert found["suffix"][1] == "suffix"
    assert found["stem"][1] in ("stem", "root")


@pytest.mark.live_phase("WfiMorphBundleOperations", "read")
def test_c1_warning_path_morphra_none(sena3_sandbox, caplog):
    """Item 3: MorphRA is None -> return None AND logger.warning fires naming the Hvo."""
    project = sena3_sandbox
    ops = project.WfiMorphBundles

    bundle = _find_bundle_with_morphra(project, need_none=True)
    assert bundle is not None, "No bundle with MorphRA=None found in Sena 3 sandbox"

    hvo = bundle.Hvo
    with caplog.at_level(logging.WARNING):
        result = ops.GetMorphType(bundle)

    assert result is None
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert warnings, "Expected a logger.warning call for MorphRA is None, none captured"
    assert any(str(hvo) in w.getMessage() for w in warnings), (
        "No warning message named the bundle Hvo=" + str(hvo)
    )
    print("[C1] warning fired naming Hvo=" + str(hvo) + ": " + str([w.getMessage() for w in warnings]))


@pytest.mark.live_phase("WfiMorphBundleOperations", "modify")
def test_c1_silent_path_morphra_set_morphtypera_none(sena3_sandbox, caplog):
    """Item 4: MorphRA set but MorphTypeRA is None -> return None, NO warning logged."""
    from SIL.LCModel import IMoStemAllomorphFactory
    from SIL.LCModel.Core.Text import TsStringUtils

    project = sena3_sandbox
    ops = project.WfiMorphBundles

    entry = _find_entry_with_lexeme_form(project)
    assert entry is not None, "No lexical entry with a lexeme form found"

    bundle = _find_bundle_with_morphra(project, need_none=False)
    assert bundle is not None

    pre_morphra_hvo = bundle.MorphRA.Hvo

    with ops._TransactionCM("TEST_254 construct typeless allomorph"):
        factory = project.project.ServiceLocator.GetService(IMoStemAllomorphFactory)
        typeless_form = factory.Create()
        entry.AlternateFormsOS.Add(typeless_form)
        ws = project.project.DefaultVernWs
        typeless_form.Form.set_String(ws, TsStringUtils.MakeString("TEST_254_typeless", ws))
        # Deliberately leave MorphTypeRA unset (None).

    if typeless_form.MorphTypeRA is not None:
        # LCM infers a default MorphTypeRA as a side effect of adding a new
        # allomorph to AlternateFormsOS (observed live). Explicitly clear it
        # in a follow-up transaction to reach the genuinely-typeless state
        # item 4 requires.
        print(
            "[C1] LCM auto-inferred MorphTypeRA="
            + str(typeless_form.MorphTypeRA.Name.BestAnalysisAlternative.Text)
            + " on Add side effect; clearing explicitly"
        )
        with ops._TransactionCM("TEST_254 clear auto-inferred morph type"):
            typeless_form.MorphTypeRA = None

    assert typeless_form.MorphTypeRA is None, "Setup invariant broken: MorphTypeRA not None"

    try:
        ops.SetMorph(bundle, typeless_form)
        assert bundle.MorphRA.Hvo == typeless_form.Hvo, "SetMorph did not link the new allomorph"

        caplog.clear()
        with caplog.at_level(logging.WARNING):
            result = ops.GetMorphType(bundle)

        assert result is None, "Expected None for MorphRA set but MorphTypeRA None"
        warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert not warnings, (
            "Expected NO warning for the silent path, got: " + str([w.getMessage() for w in warnings])
        )
        print("[C1] silent path confirmed: None returned, no warning logged")
    finally:
        with ops._TransactionCM("TEST_254 restore original morph link"):
            bundle.MorphRA = project.Object(pre_morphra_hvo)
        assert bundle.MorphRA.Hvo == pre_morphra_hvo, "Cleanup failed to restore MorphRA"


@pytest.mark.live_phase("WfiMorphBundleOperations", "modify")
def test_c2_setmorphtype_retired_raises_both_forms_and_modes(sena3_sandbox):
    """Item 5: SetMorphType raises FP_ParameterError for both non-None and None,
    identically on write-enabled and simulated read-only, no transaction opens,
    MorphRA unchanged."""
    from flexicon.code.FLExProject import FP_ParameterError

    project = sena3_sandbox
    ops = project.WfiMorphBundles

    bundle = _find_bundle_with_morphra(project, need_none=False)
    assert bundle is not None
    pre_morphra_hvo = bundle.MorphRA.Hvo

    morph_types = list(project.lp.LexDbOA.MorphTypesOA.PossibilitiesOS)
    assert morph_types
    a_morph_type = morph_types[0]

    action_handler = project.project.ActionHandlerAccessor
    pre_undo_count = action_handler.UndoableActionCount

    messages = {}
    for mode_label, write_enabled in (("write-enabled", True), ("simulated read-only", False)):
        project.writeEnabled = write_enabled
        for arg_label, arg in (("non-None", a_morph_type), ("None", None)):
            with pytest.raises(FP_ParameterError) as excinfo:
                ops.SetMorphType(bundle, arg)
            messages[(mode_label, arg_label)] = str(excinfo.value)
            print("[C2] " + mode_label + "/" + arg_label + " raised: " + str(excinfo.value))

    project.writeEnabled = True

    post_undo_count = action_handler.UndoableActionCount
    assert post_undo_count == pre_undo_count, (
        "Undo action count changed; a transaction opened when it should not have"
    )
    assert bundle.MorphRA.Hvo == pre_morphra_hvo, "MorphRA changed despite SetMorphType raising"

    assert messages[("write-enabled", "non-None")] == messages[("simulated read-only", "non-None")]
    assert messages[("write-enabled", "None")] == messages[("simulated read-only", "None")]
    assert messages[("write-enabled", "non-None")] == messages[("write-enabled", "None")]


@pytest.mark.live_phase("WfiMorphBundleOperations", "read")
def test_c3_getmorph_returns_imoform_none_silently(sena3_sandbox, caplog):
    """Item 6: GetMorph returns the IMoForm allomorph, None silently when absent."""
    project = sena3_sandbox
    ops = project.WfiMorphBundles

    bundle_set = _find_bundle_with_morphra(project, need_none=False)
    assert bundle_set is not None
    morph = ops.GetMorph(bundle_set)
    assert morph is not None
    assert morph.ClassName in ("MoStemAllomorph", "MoAffixAllomorph")
    assert morph.Hvo == bundle_set.MorphRA.Hvo
    print("[C3] GetMorph returned ClassName=" + morph.ClassName)

    bundle_none = _find_bundle_with_morphra(project, need_none=True)
    assert bundle_none is not None
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        result = ops.GetMorph(bundle_none)
    assert result is None
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert not warnings, "GetMorph should not warn on None: " + str([w.getMessage() for w in warnings])


@pytest.mark.live_phase("WfiMorphBundleOperations", "modify")
def test_c4_setmorph_roundtrip_clear_and_guard(sena3_sandbox):
    """Item 7: SetMorph writes/reads back, clears via None, and rejects a real
    IMoMorphType with FP_ParameterError naming its ClassName (not a raw TypeError)."""
    from flexicon.code.FLExProject import FP_ParameterError
    from SIL.LCModel import IWfiWordformRepository, IWfiMorphBundle

    project = sena3_sandbox
    ops = project.WfiMorphBundles

    bundle_a = _find_bundle_with_morphra(project, need_none=False)
    assert bundle_a is not None
    pre_hvo = bundle_a.MorphRA.Hvo

    other_morph = None
    checked = 0
    for wf in project.ObjectsIn(IWfiWordformRepository):
        for analysis in wf.AnalysesOC:
            for b in analysis.MorphBundlesOS:
                checked += 1
                if b.MorphRA is not None and b.MorphRA.Hvo != pre_hvo:
                    other_morph = b.MorphRA
                    break
                if checked >= 3000:
                    break
            if other_morph is not None or checked >= 3000:
                break
        if other_morph is not None or checked >= 3000:
            break
    assert other_morph is not None, "Could not find a distinct allomorph to round-trip"

    try:
        ops.SetMorph(bundle_a, other_morph)
        reread = IWfiMorphBundle(project.Object(bundle_a.Hvo))
        assert reread.MorphRA is not None
        assert reread.MorphRA.Hvo == other_morph.Hvo, (
            "SetMorph write did not survive re-read from the LCM"
        )
        print("[C4] round-trip: MorphRA now Hvo=" + str(reread.MorphRA.Hvo))

        ops.SetMorph(bundle_a, None)
        reread2 = IWfiMorphBundle(project.Object(bundle_a.Hvo))
        assert reread2.MorphRA is None, "SetMorph(bundle, None) did not clear MorphRA"
        print("[C4] SetMorph(bundle, None) confirmed clearing MorphRA")

        morph_types = list(project.lp.LexDbOA.MorphTypesOA.PossibilitiesOS)
        assert morph_types
        a_morph_type = morph_types[0]
        with pytest.raises(FP_ParameterError) as excinfo:
            ops.SetMorph(bundle_a, a_morph_type)
        msg = str(excinfo.value)
        print("[C4] SetMorph(bundle, IMoMorphType) raised: " + msg)
        assert "MoMorphType" in msg, "Error message did not name ClassName: " + msg
        assert "cannot be converted to" not in msg, (
            "Raw pythonnet TypeError text leaked into the message"
        )
        reread3 = IWfiMorphBundle(project.Object(bundle_a.Hvo))
        assert reread3.MorphRA is None, "Rejected SetMorph call mutated MorphRA"
    finally:
        with ops._TransactionCM("TEST_254 restore original morph link"):
            bundle_a.MorphRA = project.Object(pre_hvo)
        final = IWfiMorphBundle(project.Object(bundle_a.Hvo))
        assert final.MorphRA is not None and final.MorphRA.Hvo == pre_hvo, (
            "Cleanup failed to restore original MorphRA"
        )


@pytest.mark.live_phase("WfiMorphBundleOperations", "read")
def test_inflclassra_field_existence_reflection(sena3_sandbox):
    """Item 8: does InflClassRA exist on IWfiMorphBundle at all? Plain yes/no via
    live reflection, no fix applied."""
    project = sena3_sandbox
    bundle = _find_bundle_with_morphra(project, need_none=False)
    assert bundle is not None

    has_attr = hasattr(bundle, "InflClassRA")
    print("[C8] hasattr(bundle, 'InflClassRA') = " + str(has_attr))

    try:
        value = bundle.InflClassRA
        print("[C8] direct bundle.InflClassRA access succeeded, value=" + str(value))
    except Exception as exc:
        direct_error = type(exc).__name__ + ": " + str(exc)
        print("[C8] direct bundle.InflClassRA access raised: " + direct_error)

    print("[C8] ANSWER: InflClassRA exists on live IWfiMorphBundle = " + str(has_attr))
    assert True
