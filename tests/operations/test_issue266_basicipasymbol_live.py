#
#   test_issue266_basicipasymbol_live.py
#
#   Class: TestBasicIPASymbolWsCaseDivergenceLive
#          Live verification for issue #266: routing
#          PhonemeOperations.__ApplyBasicIPASymbol's target writing-system
#          lookup through BaseOperations._resolve_ws_handle, exercised
#          against a real LCM project.
#
#   Mirrors the shape of tests/operations/test_issue250_ws_case_divergence.py
#   (the sibling D4-T3 live test for the already-closed
#   BaseOperations._apply_props_loop site), adapted to
#   PhonemeOperations.ApplySyncableProperties's BasicIPASymbol path.
#
#   Project: target_sandbox ONLY (fresh tempdir copy of the Target
#   .fwbackup) -- never the in-place Target, never Sena 3. Every created
#   object is prefixed TEST_ and deleted in a `finally:` block.
#
#   Live inventory note (recorded in
#   specs/250-writingsystem-activation/evidence/live-266-basicipasymbol.md):
#   target_sandbox's only two active writing systems are 'en' (analysis,
#   handle 999000001) and 'etu' (vernacular, handle 999000002) -- neither
#   contains '-' or '_', so separator divergence (D4-c shape) cannot be
#   constructed live from this project's WS inventory. Case divergence
#   ('etu' vs 'ETU') CAN be constructed and is what this file proves live;
#   separator divergence is covered offline only, in
#   tests/operations/test_issue266_phoneme_ws_resolution.py.
#
#   Invocation (never bare `pytest` -- see tests/LIVE_TESTING.md):
#     $env:FLEXLIBS_REQUIRE_LIVE = "1"
#     python -m pytest tests/operations/test_issue266_basicipasymbol_live.py \
#         -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_266_"


def _refetch_phoneme(project, hvo):
    """Re-fetch the phoneme fresh from the LCM cache by Hvo and cast back
    to IPhPhoneme -- project.Object() returns the generic ICmObject base.
    Never reuse a stale pre-write reference; always re-resolve against the
    cache. Imports SIL.LCModel lazily so this module collects even on a
    machine without FieldWorks installed (mirrors
    test_issue250_ws_case_divergence.py's _refetch_pos convention)."""
    from SIL.LCModel import IPhPhoneme

    return IPhPhoneme(project.Object(hvo))


@pytest.fixture
def _ws_case_divergence_ctx(target_sandbox):
    """
    Record the C-D4-6-style pre-run baseline (WS count, CurVernWss,
    CurAnalysisWss) and confirm the case-divergence trigger this project's
    WS inventory can actually construct: target_sandbox's vernacular WS
    'etu' (handle 999000002) case-flips to 'ETU', a spelling genuinely
    absent from target_ws_by_id under exact matching.
    """
    project = target_sandbox
    all_ids = [(ws.Id, ws.Handle) for ws in project.WritingSystems.GetAll()]
    ws_map_by_id = dict(all_ids)

    vern_handle = project.project.DefaultVernWs
    vern_id = next((wid for wid, h in all_ids if h == vern_handle), None)
    if vern_id is None:
        pytest.skip(
            "LOUD SKIP: could not find the default vernacular ws.Id in "
            f"target_sandbox's WritingSystems.GetAll() (all_ids={all_ids})."
        )

    flipped_case = vern_id.swapcase()
    if flipped_case == vern_id:
        pytest.skip(
            f"LOUD SKIP: default vernacular ws.Id {vern_id!r} has no "
            "case-flippable character (swapcase() is a no-op) -- cannot "
            "construct a case-divergent BasicIPASymbol spelling from this "
            "project's writing systems."
        )
    if flipped_case in ws_map_by_id:
        pytest.skip(
            f"LOUD SKIP: the case-flipped spelling {flipped_case!r} is "
            "ITSELF an exact-case key in this project's WritingSystems -- "
            "would hit step 1 (exact match) instead of exercising the "
            "normalized fallback this test targets."
        )

    return {
        "project": project,
        "vern_id": vern_id,
        "vern_handle": vern_handle,
        "flipped_case": flipped_case,
        "pre_run_ws_count": len(all_ids),
        "pre_run_cur_vern_wss": project.lp.CurVernWss,
        "pre_run_cur_analysis_wss": project.lp.CurAnalysisWss,
    }


def _assert_ws_store_unchanged(ctx):
    """The fix must never activate, create, or widen the writing-system
    store (spec 250 C-D4-6, carried over per issue #266)."""
    project = ctx["project"]
    post_ids = [(ws.Id, ws.Handle) for ws in project.WritingSystems.GetAll()]
    assert len(post_ids) == ctx["pre_run_ws_count"], (
        "Writing-system count changed across the run -- the fix must "
        "never activate or create a writing system."
    )
    assert project.lp.CurVernWss == ctx["pre_run_cur_vern_wss"], (
        "CurVernWss changed across the run."
    )
    assert project.lp.CurAnalysisWss == ctx["pre_run_cur_analysis_wss"], (
        "CurAnalysisWss changed across the run."
    )


class TestBasicIPASymbolWsCaseDivergenceLive:
    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_case_divergent_basicipasymbol_alt_resolves_and_saves(
        self, _ws_case_divergence_ctx
    ):
        """
        Issue #266's exact reproducer: a source dict spells the target
        vernacular writing system in the wrong case ('ETU' where the
        project's real ws.Id is 'etu'). Pre-fix, __ApplyBasicIPASymbol's
        own exact-case-only `target_ws_by_id.get(tgt_ws_id)` misses and
        the alt is silently dropped. Post-fix it resolves through
        `_resolve_ws_handle`'s normalized fallback and saves.
        """
        ctx = _ws_case_divergence_ctx
        project = ctx["project"]
        phoneme_ops = project.Phonemes

        phoneme = phoneme_ops.Create(f"{TEST_PREFIX}{ctx['vern_handle']}")
        hvo = phoneme.Hvo
        try:
            pre = phoneme_ops.GetBasicIPASymbol(
                _refetch_phoneme(project, hvo), ctx["vern_handle"]
            )
            assert pre == "", (
                f"Pre-state: BasicIPASymbol alt at handle "
                f"{ctx['vern_handle']} (ws_id={ctx['vern_id']!r}) must be "
                f"empty before apply; got {pre!r}."
            )

            phoneme_ops.ApplySyncableProperties(
                phoneme,
                {"BasicIPASymbol": {ctx["flipped_case"]: "TEST_266_ipa"}},
            )

            post_phoneme = _refetch_phoneme(project, hvo)  # fresh re-fetch
            post = phoneme_ops.GetBasicIPASymbol(post_phoneme, ctx["vern_handle"])

            assert post == "TEST_266_ipa", (
                "#266: source key "
                f"{ctx['flipped_case']!r} (case-divergent from the "
                f"target's real ws.Id {ctx['vern_id']!r}) must resolve to "
                f"handle {ctx['vern_handle']} and save the BasicIPASymbol "
                f"text. Got {post!r} -- if this is empty, the fix did not "
                "land or did not reach __ApplyBasicIPASymbol."
            )

            _assert_ws_store_unchanged(ctx)
        finally:
            phoneme_ops.Delete(phoneme)

    @pytest.mark.live_phase("PhonemeOperations", "modify")
    def test_exact_match_still_saves_unchanged(self, _ws_case_divergence_ctx):
        """
        Zero-regression control: an exact-case spelling must still save
        exactly as before the fix (step 1 of _resolve_ws_handle is
        byte-for-byte the pre-fix exact-match path)."""
        ctx = _ws_case_divergence_ctx
        project = ctx["project"]
        phoneme_ops = project.Phonemes

        phoneme = phoneme_ops.Create(f"{TEST_PREFIX}exact_{ctx['vern_handle']}")
        hvo = phoneme.Hvo
        try:
            phoneme_ops.ApplySyncableProperties(
                phoneme, {"BasicIPASymbol": {ctx["vern_id"]: "TEST_266_exact"}}
            )

            post_phoneme = _refetch_phoneme(project, hvo)
            post = phoneme_ops.GetBasicIPASymbol(post_phoneme, ctx["vern_handle"])

            assert post == "TEST_266_exact", (
                f"Exact-case spelling {ctx['vern_id']!r} must still save "
                f"unchanged. Got {post!r}."
            )

            _assert_ws_store_unchanged(ctx)
        finally:
            phoneme_ops.Delete(phoneme)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
