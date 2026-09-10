#
#   test_issue267_translations_live.py
#
#   Class: TestTranslationsOCWsCaseDivergenceLive
#          Live verification for issue #267: routing
#          ExampleOperations.ApplySyncableProperties's TranslationsOC loop
#          target writing-system lookup through BaseOperations
#          ._resolve_ws_handle, WITHOUT orphaning a zero-alt
#          ICmTranslation, exercised against a real LCM project.
#
#   Mirrors the shape of tests/operations/test_issue266_basicipasymbol_live.py
#   (the sibling site's own live coverage), adapted to
#   ExampleOperations.ApplySyncableProperties's TranslationsOC path.
#
#   Project: target_sandbox ONLY (fresh tempdir copy of the Target
#   .fwbackup) -- never the in-place Target, never Sena 3. Every created
#   object is prefixed TEST_267_ and deleted in a `finally:` block.
#
#   Live inventory note (matches #266's own disclosure,
#   specs/250-writingsystem-activation/evidence/live-266-basicipasymbol.md):
#   target_sandbox's only two active writing systems are 'en' (analysis,
#   handle 999000001) and 'etu' (vernacular, handle 999000002) -- neither
#   contains '-' or '_', so separator divergence cannot be constructed
#   live from this project's WS inventory, and a genuinely ambiguous
#   normalized match (two DISTINCT active writing systems that normalize
#   to the same form) cannot be constructed either, since FieldWorks does
#   not offer a way to activate a second writing system whose Id differs
#   from an already-active one only by case -- BCP-47 tags are
#   case-normalized on creation. Case divergence ('en' vs 'EN') CAN be
#   constructed and is what this file proves live. Separator divergence
#   and the ambiguity-raise/orphan-prevention mechanics are covered
#   offline only, in tests/operations/test_issue267_translations_ws_resolution.py.
#
#   Invocation (never bare `pytest` -- see tests/LIVE_TESTING.md):
#     $env:FLEXLIBS_REQUIRE_LIVE = "1"
#     python -m pytest tests/operations/test_issue267_translations_live.py \
#         -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_267_"


def _first_translation(example):
    """Return the first ICmTranslation in example.TranslationsOC via
    iteration, not indexing -- ICmTranslationOC's indexer has produced a
    pythonnet "SystemError: error return without exception set" in this
    environment, while plain iteration works reliably."""
    for trans in example.TranslationsOC:
        return trans
    return None


def _refetch_example(project, hvo):
    """Re-fetch the example fresh from the LCM cache by Hvo and cast back
    to ILexExampleSentence -- project.Object() returns the generic
    ICmObject base. Never reuse a stale pre-write reference; always
    re-resolve against the cache. Imports SIL.LCModel lazily so this
    module collects even on a machine without FieldWorks installed
    (mirrors test_issue266_basicipasymbol_live.py's _refetch_phoneme
    convention)."""
    from SIL.LCModel import ILexExampleSentence

    return ILexExampleSentence(project.Object(hvo))


@pytest.fixture
def _ws_case_divergence_ctx(target_sandbox):
    """
    Record the C-D4-6-style pre-run baseline (WS count, CurVernWss,
    CurAnalysisWss) and confirm the case-divergence trigger this project's
    WS inventory can actually construct: target_sandbox's default analysis
    WS 'en' (handle 999000001) case-flips to 'EN', a spelling genuinely
    absent from target_ws_by_id under exact matching. Also creates the
    TEST_267_ lexical entry/sense/example scaffold every test in this file
    needs, and a TypeRA GUID drawn from the project's own
    TranslationTagsOA (so the test does not hardcode a possibility list
    layout that could drift).
    """
    project = target_sandbox
    all_ids = [(ws.Id, ws.Handle) for ws in project.WritingSystems.GetAll()]
    ws_map_by_id = dict(all_ids)

    anal_handle = project.project.DefaultAnalWs
    anal_id = next((wid for wid, h in all_ids if h == anal_handle), None)
    if anal_id is None:
        pytest.skip(
            "LOUD SKIP: could not find the default analysis ws.Id in "
            f"target_sandbox's WritingSystems.GetAll() (all_ids={all_ids})."
        )

    flipped_case = anal_id.swapcase()
    if flipped_case == anal_id:
        pytest.skip(
            f"LOUD SKIP: default analysis ws.Id {anal_id!r} has no "
            "case-flippable character (swapcase() is a no-op) -- cannot "
            "construct a case-divergent Translation spelling from this "
            "project's writing systems."
        )
    if flipped_case in ws_map_by_id:
        pytest.skip(
            f"LOUD SKIP: the case-flipped spelling {flipped_case!r} is "
            "ITSELF an exact-case key in this project's WritingSystems -- "
            "would hit step 1 (exact match) instead of exercising the "
            "normalized fallback this test targets."
        )

    type_objs = list(project.lp.TranslationTagsOA.PossibilitiesOS)
    if not type_objs:
        pytest.skip(
            "LOUD SKIP: target_sandbox's TranslationTagsOA has no "
            "possibilities -- cannot construct a TypeRA-bearing "
            "ICmTranslation."
        )
    type_guid = str(type_objs[0].Guid)

    entry = project.LexEntry.Create(f"{TEST_PREFIX}entry")
    sense = entry.SensesOS[0]

    ctx = {
        "project": project,
        "entry": entry,
        "sense": sense,
        "anal_id": anal_id,
        "anal_handle": anal_handle,
        "flipped_case": flipped_case,
        "type_guid": type_guid,
        "pre_run_ws_count": len(all_ids),
        "pre_run_cur_vern_wss": project.lp.CurVernWss,
        "pre_run_cur_analysis_wss": project.lp.CurAnalysisWss,
    }
    try:
        yield ctx
    finally:
        project.LexEntry.Delete(entry)


def _assert_ws_store_unchanged(ctx):
    """The fix must never activate, create, or widen the writing-system
    store (spec 250 C-D4-6, carried over per issue #267)."""
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


class TestTranslationsOCWsCaseDivergenceLive:
    @pytest.mark.live_phase("ExampleOperations", "modify")
    def test_case_divergent_translation_alt_resolves_and_saves(
        self, _ws_case_divergence_ctx
    ):
        """
        Issue #267's exact reproducer: a source dict spells the target
        analysis writing system in the wrong case ('EN' where the
        project's real ws.Id is 'en'). Pre-fix, the TranslationsOC loop's
        own exact-case-only `target_ws_by_id.get(tgt_ws_id)` misses and
        the alt is silently dropped (the ICmTranslation is still created,
        but with zero alts). Post-fix it resolves through
        `_resolve_ws_handle`'s normalized fallback and saves.
        """
        ctx = _ws_case_divergence_ctx
        project = ctx["project"]

        example = project.Examples.Create(ctx["sense"], f"{TEST_PREFIX}example")
        hvo = example.Hvo

        pre = _refetch_example(project, hvo)
        assert pre.TranslationsOC.Count == 0, (
            "Pre-state: example must start with no translations."
        )

        project.Examples.ApplySyncableProperties(
            example,
            {
                "TranslationsOC": [
                    {
                        "Translation": {ctx["flipped_case"]: "TEST_267_trans_case"},
                        "TypeRA": ctx["type_guid"],
                    }
                ]
            },
        )

        post = _refetch_example(project, hvo)  # fresh re-fetch
        assert post.TranslationsOC.Count == 1, (
            f"Expected exactly one ICmTranslation after apply; got "
            f"{post.TranslationsOC.Count}."
        )
        saved_text = _first_translation(post).Translation.get_String(
            ctx["anal_handle"]
        ).Text

        assert saved_text == "TEST_267_trans_case", (
            "#267: source key "
            f"{ctx['flipped_case']!r} (case-divergent from the target's "
            f"real ws.Id {ctx['anal_id']!r}) must resolve to handle "
            f"{ctx['anal_handle']} and save the Translation text. Got "
            f"{saved_text!r} -- if this is None/empty, the fix did not "
            "land or did not reach the TranslationsOC loop."
        )

        _assert_ws_store_unchanged(ctx)

    @pytest.mark.live_phase("ExampleOperations", "modify")
    def test_exact_match_still_saves_unchanged(self, _ws_case_divergence_ctx):
        """
        Zero-regression control: an exact-case spelling must still save
        exactly as before the fix (step 1 of _resolve_ws_handle is
        byte-for-byte the pre-fix exact-match path)."""
        ctx = _ws_case_divergence_ctx
        project = ctx["project"]

        example = project.Examples.Create(
            ctx["sense"], f"{TEST_PREFIX}example_exact"
        )
        hvo = example.Hvo

        project.Examples.ApplySyncableProperties(
            example,
            {
                "TranslationsOC": [
                    {
                        "Translation": {ctx["anal_id"]: "TEST_267_trans_exact"},
                        "TypeRA": ctx["type_guid"],
                    }
                ]
            },
        )

        post = _refetch_example(project, hvo)
        saved_text = _first_translation(post).Translation.get_String(
            ctx["anal_handle"]
        ).Text

        assert saved_text == "TEST_267_trans_exact", (
            f"Exact-case spelling {ctx['anal_id']!r} must still save "
            f"unchanged. Got {saved_text!r}."
        )

        _assert_ws_store_unchanged(ctx)

    @pytest.mark.live_phase("ExampleOperations", "modify")
    def test_genuine_miss_still_skips_but_now_logs_a_warning(
        self, _ws_case_divergence_ctx, caplog
    ):
        """
        A target writing system genuinely absent from the project (under
        both exact and normalized matching) still skips (Defect 3,
        unchanged) -- the ICmTranslation is still created (a TypeRA-only
        translation is a legitimate pre-existing shape), but carries no
        alt. What changed: the drop is no longer silent."""
        ctx = _ws_case_divergence_ctx
        project = ctx["project"]

        example = project.Examples.Create(ctx["sense"], f"{TEST_PREFIX}example_miss")
        hvo = example.Hvo

        with caplog.at_level("WARNING"):
            project.Examples.ApplySyncableProperties(
                example,
                {
                    "TranslationsOC": [
                        {
                            "Translation": {"de-DE": "TEST_267_trans_miss"},
                            "TypeRA": ctx["type_guid"],
                        }
                    ]
                },
            )

        post = _refetch_example(project, hvo)
        assert post.TranslationsOC.Count == 1
        saved_text = _first_translation(post).Translation.get_String(
            ctx["anal_handle"]
        ).Text
        assert not saved_text, (
            f"'de-DE' is genuinely absent from target_sandbox's WS "
            f"inventory; expected no alt written at the analysis handle. "
            f"Got {saved_text!r}."
        )

        warnings = [
            r for r in caplog.records
            if "de-DE" in r.getMessage() and "ICmTranslation.Translation" in r.getMessage()
        ]
        assert warnings, (
            "Expected an unconditional warning naming the dropped 'de-DE' "
            "alt; none was logged."
        )

        _assert_ws_store_unchanged(ctx)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
