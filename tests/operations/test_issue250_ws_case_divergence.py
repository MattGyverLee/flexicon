#
#   test_issue250_ws_case_divergence.py
#
#   Class: TestWsCaseDivergenceLive
#          Live verification for issue #250 Defect 4 (D4-T3):
#          BaseOperations._apply_props_loop's normalized writing-system
#          resolution fallback, exercised against a real LCM project.
#
#   Shape frozen in specs/250-writingsystem-activation/spec.md section 6.4.
#   Project: target_sandbox ONLY (fresh tempdir copy of the Target
#   .fwbackup) -- never the in-place Target, never Sena 3. Every created
#   object is prefixed TEST_.
#
#   Predictions for both the unfixed-code run and the fixed-code run are
#   committed in
#   specs/250-writingsystem-activation/evidence/live-D4-T3.md BEFORE this
#   file is executed against either state of BaseOperations.py.
#
#   Coverage boundary (acceptance criterion 8, spec 250): this test proves
#   the fix reaches BaseOperations._apply_props_loop ONLY. It does not
#   exercise, and cannot prove anything about,
#   Grammar/PhonemeOperations.__ApplyBasicIPASymbol or
#   Lexicon/ExampleOperations.ApplySyncableProperties's TranslationsOC
#   loop -- both remain self-resolving and out of scope (spec section 1.2,
#   C-D4-2, findings F2/F5).
#
#   Invocation (never bare `pytest` -- see tests/LIVE_TESTING.md):
#     $env:FLEXLIBS_REQUIRE_LIVE = "1"
#     python -m pytest tests/operations/test_issue250_ws_case_divergence.py \
#         -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def _refetch_pos(project, hvo):
    """Re-fetch the POS fresh from the LCM cache by Hvo and cast back to
    IPartOfSpeech -- project.Object() returns the generic ICmObject/
    ICmPossibility base, which has no .Name attribute. Never reuse a
    stale pre-write reference; this always re-resolves against the cache.

    Imports SIL.LCModel lazily (inside the function, not at module scope)
    so this module can be collected even on a machine without FieldWorks
    installed -- mirrors the existing convention in
    test_apply_syncable_properties.py's live section."""
    from SIL.LCModel import IPartOfSpeech

    return IPartOfSpeech(project.Object(hvo))


def _swap_case_flip(tag):
    """Case-flip a ws.Id, e.g. 'en' -> 'EN', 'en-US' -> 'EN-us'."""
    return tag.swapcase()


def _separator_flip(tag):
    """Flip the separator convention of a ws.Id: hyphen <-> underscore."""
    if "-" in tag:
        return tag.replace("-", "_")
    if "_" in tag:
        return tag.replace("_", "-")
    return tag


def _pick_non_default_analysis_ws(project):
    """
    Pick a (ws_id, handle) pair from the project's active writing systems
    whose handle is NOT the default analysis WS. POSOperations.Create()
    always writes Name/Abbreviation into the default analysis WS, so a
    newly-created POS's Name alt at any OTHER handle is guaranteed empty
    pre-write -- which is what the pre-state assertion needs.

    Returns (ws_id, handle, all_ids) where all_ids is the full
    [(Id, Handle), ...] list recorded for the evidence file.
    """
    all_ids = [(ws.Id, ws.Handle) for ws in project.WritingSystems.GetAll()]
    default_anal_handle = project.project.DefaultAnalWs
    for ws_id, handle in all_ids:
        if handle != default_anal_handle:
            return ws_id, handle, all_ids
    return None, None, all_ids


@pytest.fixture
def _case_divergence_fixture(target_sandbox):
    """
    Shared setup for all three D4 variants: pick a non-default-analysis
    writing system, derive its case-flipped and separator-flipped
    spellings, and record the C-D4-6 pre-run baseline (WS count,
    CurVernWss, CurAnalysisWss).
    """
    project = target_sandbox
    ws_id, handle, all_ids = _pick_non_default_analysis_ws(project)
    if ws_id is None:
        pytest.skip(
            "LOUD SKIP: target_sandbox has only one active writing system "
            "(the default analysis WS) -- no second WS available to prove "
            "an empty pre-write Name alt. This is a project-fixture gap, "
            "not a silent pass."
        )

    flipped_case = _swap_case_flip(ws_id)
    if flipped_case == ws_id:
        pytest.skip(
            f"LOUD SKIP: ws.Id {ws_id!r} has no case-flippable character "
            "(swapcase() is a no-op) -- cannot construct a case-divergent "
            "spelling from this project's writing systems."
        )

    # flipped_sep is deliberately NOT gated here: D4-a and D4-b (the only
    # variants that use flipped_case) must not skip just because this
    # project's picked ws_id happens to have no '-'/'_' separator to flip
    # (e.g. a bare single-subtag Id like 'etu'). The separator-flippability
    # check lives in the D4-c test itself, which is the only variant that
    # needs it -- see that test's own loud skip.
    flipped_sep = _separator_flip(ws_id)

    pre_run_ws_count = len(all_ids)
    pre_run_cur_vern_wss = project.lp.CurVernWss
    pre_run_cur_analysis_wss = project.lp.CurAnalysisWss

    return {
        "project": project,
        "ws_id": ws_id,
        "handle": handle,
        "all_ids": all_ids,
        "flipped_case": flipped_case,
        "flipped_sep": flipped_sep,
        "pre_run_ws_count": pre_run_ws_count,
        "pre_run_cur_vern_wss": pre_run_cur_vern_wss,
        "pre_run_cur_analysis_wss": pre_run_cur_analysis_wss,
    }


def _assert_cd4_6_unchanged(ctx):
    """C-D4-6: writing-system count and CurVernWss/CurAnalysisWss must be
    byte-identical to their pre-run values -- the fix never activates,
    never creates, never widens the store."""
    project = ctx["project"]
    post_ids = [(ws.Id, ws.Handle) for ws in project.WritingSystems.GetAll()]
    assert len(post_ids) == ctx["pre_run_ws_count"], (
        "Writing-system count changed across the run -- Defect 4 must "
        "never activate or create a writing system (C-D4-6)."
    )
    assert project.lp.CurVernWss == ctx["pre_run_cur_vern_wss"], (
        "CurVernWss changed across the run (C-D4-6 violation)."
    )
    assert project.lp.CurAnalysisWss == ctx["pre_run_cur_analysis_wss"], (
        "CurAnalysisWss changed across the run (C-D4-6 violation)."
    )


class TestWsCaseDivergenceLive:
    """
    Each test creates its own throwaway TEST_-prefixed POS so that the
    pre-state ("Name alt empty at `handle`") is genuinely guaranteed for
    that test, independent of any other test's writes in this file
    (spec section 6.4 describes these steps against a shared object;
    this file uses one object per D4 variant instead, so a fixed/unfixed
    comparison of each variant is never polluted by a prior variant's
    write to the same writing-system alt -- see evidence file for the
    rationale recorded per instruction).
    """

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_d4a_ws_map_case_divergent_resolves(self, _case_divergence_fixture):
        ctx = _case_divergence_fixture
        project = ctx["project"]
        pos_ops = project.POS

        pos = pos_ops.Create(f"{TEST_PREFIX}D4a_{ctx['handle']}", "TD4a")
        hvo = pos.Hvo
        try:
            pre = pos_ops.GetName(_refetch_pos(project, hvo), ctx["handle"])
            assert pre == "", (
                f"Pre-state: Name alt at handle {ctx['handle']} "
                f"(ws_id={ctx['ws_id']!r}) must be empty before apply; "
                f"got {pre!r}."
            )

            pos_ops.ApplySyncableProperties(
                pos,
                {"Name": {"en": "TEST_D4a"}},
                ws_map={"en": ctx["flipped_case"]},
            )

            post_pos = _refetch_pos(project, hvo)  # re-fetch fresh, not the stale ref
            post = pos_ops.GetName(post_pos, ctx["handle"])

            assert post == "TEST_D4a", (
                "D4-a: ws_map value 'en' -> "
                f"{ctx['flipped_case']!r} (case-divergent from the "
                f"target's real ws.Id {ctx['ws_id']!r}) must resolve to "
                f"handle {ctx['handle']} and save the text. Got {post!r} "
                "-- if this is empty, the fix did not land or did not "
                "reach this call path."
            )

            _assert_cd4_6_unchanged(ctx)
        finally:
            pos_ops.Delete(pos)

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_d4b_no_ws_map_source_id_case_divergent_resolves(
        self, _case_divergence_fixture
    ):
        ctx = _case_divergence_fixture
        project = ctx["project"]
        pos_ops = project.POS

        pos = pos_ops.Create(f"{TEST_PREFIX}D4b_{ctx['handle']}", "TD4b")
        hvo = pos.Hvo
        try:
            pre = pos_ops.GetName(_refetch_pos(project, hvo), ctx["handle"])
            assert pre == "", (
                f"Pre-state: Name alt at handle {ctx['handle']} must be "
                f"empty before apply; got {pre!r}."
            )

            # D4-b: NO ws_map at all -- src_ws_id passes through unchanged.
            pos_ops.ApplySyncableProperties(
                pos,
                {"Name": {ctx["flipped_case"]: "TEST_D4b"}},
                ws_map=None,
            )

            post_pos = _refetch_pos(project, hvo)
            post = pos_ops.GetName(post_pos, ctx["handle"])

            assert post == "TEST_D4b", (
                "D4-b: no ws_map, source key "
                f"{ctx['flipped_case']!r} (case-divergent from target's "
                f"real ws.Id {ctx['ws_id']!r}) must still resolve to "
                f"handle {ctx['handle']}. Got {post!r}."
            )

            _assert_cd4_6_unchanged(ctx)
        finally:
            pos_ops.Delete(pos)

    @pytest.mark.live_phase("POSOperations", "modify")
    def test_d4c_separator_divergent_resolves(self, _case_divergence_fixture):
        ctx = _case_divergence_fixture
        if ctx["flipped_sep"] == ctx["ws_id"]:
            pytest.skip(
                f"LOUD SKIP: ws.Id {ctx['ws_id']!r} has no '-' or '_' "
                "separator -- cannot construct a separator-divergent "
                "spelling from this project's writing systems. D4-a and "
                "D4-b (case divergence) are unaffected by this and are "
                "covered by their own tests in this file; the separator "
                "path of C-D4-5 is additionally covered offline in "
                "test_issue250_defect4_ws_resolution.py, which does not "
                "depend on any particular project's WS inventory."
            )
        project = ctx["project"]
        pos_ops = project.POS

        pos = pos_ops.Create(f"{TEST_PREFIX}D4c_{ctx['handle']}", "TD4c")
        hvo = pos.Hvo
        try:
            pre = pos_ops.GetName(_refetch_pos(project, hvo), ctx["handle"])
            assert pre == "", (
                f"Pre-state: Name alt at handle {ctx['handle']} must be "
                f"empty before apply; got {pre!r}."
            )

            pos_ops.ApplySyncableProperties(
                pos,
                {"Name": {ctx["flipped_sep"]: "TEST_D4c"}},
                ws_map=None,
            )

            post_pos = _refetch_pos(project, hvo)
            post = pos_ops.GetName(post_pos, ctx["handle"])

            assert post == "TEST_D4c", (
                "D4-c: separator-divergent source key "
                f"{ctx['flipped_sep']!r} (target's real ws.Id is "
                f"{ctx['ws_id']!r}) must resolve to handle "
                f"{ctx['handle']}. Got {post!r}."
            )

            _assert_cd4_6_unchanged(ctx)
        finally:
            pos_ops.Delete(pos)
