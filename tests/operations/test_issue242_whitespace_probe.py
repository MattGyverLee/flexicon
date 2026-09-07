#
#   test_issue242_whitespace_probe.py
#
#   CHECKPOINT 1 probe for issue #242 (specs/242-paragraph-whitespace):
#   measures whether whitespace written through the paragraph/segment text
#   writers actually survives a write-read cycle.
#
#   THE FOUR SITES UNDER STUDY:
#     flexicon/code/TextsWords/ParagraphOperations.py:171  Create
#     flexicon/code/TextsWords/ParagraphOperations.py:576  SetText
#     flexicon/code/TextsWords/ParagraphOperations.py:716  InsertAt
#     flexicon/code/TextsWords/SegmentOperations.py:589    AppendSentence
#   All four strip a copy of the incoming text for the emptiness check and
#   then persist the STRIPPED value via TsStringUtils.MakeString. Branch
#   asymmetry already found by inspection: ParagraphOperations does NOT
#   strip the non-str branch (`str(content)`), while SegmentOperations
#   DOES strip it (`str(text).strip()`) -- see test_p5 below.
#
#   This file measures the bug; it does NOT fix it. No file under
#   flexicon/code/ is touched by this task -- see
#   specs/242-paragraph-whitespace/evidence/live-probe-cycle1.md for the
#   `git diff --stat -- flexicon/` proof.
#
#   TWO MEASUREMENT LAYERS (both required):
#     Layer A (test_p1, test_p2) -- call the public writers as they ship
#       today, re-read from the LCM. Documents TODAY's loss.
#     Layer B (test_p3) -- bypass ParagraphOperations/SegmentOperations
#       entirely: build the TsString from the RAW, unstripped payload and
#       set the LCM property directly inside a transaction, then re-read.
#       If the LCM/FLEx layer normalises whitespace on its own here (with
#       none of this library's own .strip() calls anywhere in the path),
#       then #242's fix would be COSMETIC. This is the single most
#       decision-relevant number this probe produces.
#
#   ALSO MEASURED:
#     test_p4 -- IN-MEMORY vs ON-DISK: read back in-session, then close
#       and reopen the same sandbox .fwdata and read again.
#     test_p5 -- THE NON-STR BRANCH DIVERGENCE between ParagraphOperations
#       and SegmentOperations.AppendSentence.
#
#   Uses target_sandbox / target_sandbox_path (tests/conftest.py)
#   EXCLUSIVELY. Never the real Target project, never scripts/restore_*.py.
#   Every project opened via target_sandbox_path in this file is disposed
#   in a `finally:` block, matching the convention established by
#   tests/operations/test_issue243_closeproject_probe.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pathlib

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_242_"

# ---------------------------------------------------------------------------
# Payload matrix -- "whitespace" is not one thing; every entry is measured
# and reported separately, never generalised from another entry.
# ---------------------------------------------------------------------------
PAYLOADS = [
    ("trailing_space", "ka "),
    ("leading_space", " ka"),
    ("trailing_tab", "ka\t"),
    ("trailing_newline", "ka\n"),
    ("trailing_nbsp", "ka "),
    ("internal_double_space", "ka  ba"),
    ("null_marker_bare", "***"),
    ("null_marker_padded", " *** "),
]


def _safe(fn, label):
    """Run fn(), print+return (result, None) or print+return (None, 'Type: msg')."""
    try:
        result = fn()
        print(f"[PROBE] {label}: OK -> {result!r}")
        return result, None
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        print(f"[PROBE] {label}: RAISED {msg}")
        return None, msg


def _dispose_if_open(project, label):
    """Manually dispose the LCM cache if CloseProject() did not already do
    so. Idempotent: safe to call even after a successful CloseProject()."""
    if hasattr(project, "project"):
        try:
            project.project.Dispose()
            del project.project
            print(f"[PROBE] {label}: manually disposed cache")
        except Exception as exc:
            print(f"[PROBE] {label}: manual dispose also raised: {type(exc).__name__}: {exc}")


class _NonStrPayload:
    """An object whose __str__() returns a payload with trailing whitespace,
    matching the owner's real-world trailing-space case, for the non-str
    branch divergence probe (test_p5)."""

    def __str__(self):
        return "ka "


# ===========================================================================
# P-1 -- LAYER A: Create / SetText / InsertAt (ParagraphOperations)
# ===========================================================================

@pytest.mark.live_phase("ParagraphOperations", "add")
def test_p1_layer_a_paragraph_writers_matrix(target_sandbox):
    """
    CURRENT BEHAVIOUR (layer A): call Create / SetText / InsertAt as they
    ship today for every payload in the matrix, and re-read via GetText().

    All three writers share one stripping line:
        content_str = content.strip() if isinstance(content, str) else str(content)
    so they are predicted to behave IDENTICALLY to each other (unlike
    AppendSentence, which has a different line -- measured separately in
    test_p2).
    """
    project = target_sandbox
    text = project.Texts.Create(f"{TEST_PREFIX}p1_text")

    results = {}
    for label, raw in PAYLOADS:
        create_para, create_exc = _safe(
            lambda raw=raw: project.Paragraphs.Create(text, raw),
            f"P1 Create({label!r})",
        )
        create_read = project.Paragraphs.GetText(create_para) if create_para is not None else None

        para_count = text.ContentsOA.ParagraphsOS.Count
        insert_para, insert_exc = _safe(
            lambda raw=raw, idx=para_count: project.Paragraphs.InsertAt(text, idx, raw),
            f"P1 InsertAt({label!r})",
        )
        insert_read = project.Paragraphs.GetText(insert_para) if insert_para is not None else None

        seed_para, _ = _safe(
            lambda: project.Paragraphs.Create(text, "placeholder."),
            f"P1 SetText seed({label!r})",
        )
        settext_read = None
        settext_exc = None
        if seed_para is not None:
            _, settext_exc = _safe(
                lambda raw=raw, p=seed_para: project.Paragraphs.SetText(p, raw),
                f"P1 SetText({label!r})",
            )
            settext_read = project.Paragraphs.GetText(seed_para)

        row = {
            "raw": raw,
            "create": create_read, "create_exc": create_exc,
            "insert": insert_read, "insert_exc": insert_exc,
            "settext": settext_read, "settext_exc": settext_exc,
        }
        results[label] = row
        print(
            f"[TABLE][P1] {label!r}: raw={raw!r} "
            f"Create->{create_read!r} InsertAt->{insert_read!r} SetText->{settext_read!r}"
        )

    print(f"[SUMMARY][P1] full layer-A paragraph-writer table: {results}")

    # Headline sanity: all three writers strip via the SAME source line, so
    # for every payload their re-read values must agree with each other. A
    # divergence here would itself be a finding, not an expected outcome.
    for label, row in results.items():
        assert row["create_exc"] is None and row["insert_exc"] is None and row["settext_exc"] is None, (
            f"Payload {label!r}: unexpected exception -- {row}"
        )
        assert row["create"] == row["insert"] == row["settext"], (
            f"Payload {label!r} (raw={row['raw']!r}): Create/InsertAt/SetText "
            f"disagree -- {row['create']!r} vs {row['insert']!r} vs "
            f"{row['settext']!r}. They share one stripping line; a "
            f"divergence here would itself be a finding."
        )


# ===========================================================================
# P-2 -- LAYER A: AppendSentence (SegmentOperations)
# ===========================================================================

@pytest.mark.live_phase("SegmentOperations", "add")
def test_p2_layer_a_append_sentence_matrix(target_sandbox):
    """
    CURRENT BEHAVIOUR (layer A) for AppendSentence, measured separately
    from the paragraph writers because its stripping line differs:
        text_str = text.strip() if isinstance(text, str) else str(text).strip()

    Each payload gets a FRESH paragraph seeded with "Seed." so the append
    takes AppendSentence's "already terminated" branch (a single space
    separator is inserted, not ". "). Both of AppendSentence's branches
    consume the SAME already-stripped `text_str`, so exercising one branch
    is sufficient to characterise the strip itself; the
    current_length == 0 (empty-paragraph, direct-write) branch was NOT
    separately probed here -- noted explicitly rather than silently
    skipped.

    Also measures the segment BASELINE (Segments.GetBaselineText)
    independently of the paragraph Contents, per the task brief: segment
    boundary/reparse logic may trim on its own, or BeginOffset/EndOffset
    may not yet be computed immediately after AppendSentence (per the
    "will set ... when the paragraph is re-parsed" comment at
    SegmentOperations.py:639-640) -- this is UNMEASURED prior to this run.
    """
    project = target_sandbox
    text = project.Texts.Create(f"{TEST_PREFIX}p2_text")

    results = {}
    for label, raw in PAYLOADS:
        para, seed_exc = _safe(lambda: project.Paragraphs.Create(text, "Seed."), f"P2 seed para({label!r})")
        if para is None:
            results[label] = {"raw": raw, "error": f"seed paragraph creation failed: {seed_exc}"}
            continue

        seg, append_exc = _safe(
            lambda raw=raw, p=para: project.Segments.AppendSentence(p, raw),
            f"P2 AppendSentence({label!r})",
        )

        full_contents = project.Paragraphs.GetText(para)
        baseline = None
        baseline_exc = None
        if seg is not None:
            baseline, baseline_exc = _safe(
                lambda s=seg: project.Segments.GetBaselineText(s),
                f"P2 GetBaselineText({label!r})",
            )

        row = {
            "raw": raw,
            "append_exc": append_exc,
            "full_contents": full_contents,
            "baseline": baseline,
            "baseline_exc": baseline_exc,
        }
        results[label] = row
        print(
            f"[TABLE][P2] {label!r}: raw={raw!r} append_exc={append_exc!r} "
            f"full_contents={full_contents!r} baseline={baseline!r} baseline_exc={baseline_exc!r}"
        )

    print(f"[SUMMARY][P2] full layer-A AppendSentence table: {results}")

    for label, row in results.items():
        assert "error" not in row, f"Payload {label!r}: {row.get('error')}"
        assert row["append_exc"] is None, f"Payload {label!r}: AppendSentence raised: {row['append_exc']}"

    # Independent check requested by the task brief: does the segment
    # baseline agree with the tail of the paragraph Contents, or does
    # segment/reparse logic diverge from it? Reported, not asserted, since
    # this is the open question.
    for label, row in results.items():
        if row["baseline_exc"] is not None:
            print(f"[VERDICT][P2] {label!r}: GetBaselineText RAISED -- {row['baseline_exc']}")
        elif row["baseline"] and row["full_contents"] and row["full_contents"].endswith(row["baseline"]):
            print(f"[VERDICT][P2] {label!r}: segment baseline is a clean tail-match of paragraph Contents.")
        else:
            print(
                f"[VERDICT][P2] {label!r}: segment baseline does NOT cleanly tail-match "
                f"paragraph Contents -- full_contents={row['full_contents']!r} "
                f"baseline={row['baseline']!r}"
            )


# ===========================================================================
# P-3 -- LAYER B: BYPASS THE OPERATIONS LAYER ENTIRELY
# ===========================================================================

@pytest.mark.live_phase("ParagraphOperations", "modify")
def test_p3_layer_b_bypass_operations_layer(target_sandbox):
    """
    IS THE FIX EVEN POSSIBLE? Bypass ParagraphOperations/SegmentOperations
    entirely: build the TsString from the RAW, unstripped payload and set
    para.Contents directly inside a transaction, then re-read.

    If the LCM/FLEx layer normalises the whitespace on its own here (with
    NO .strip() from this library anywhere in the path), then #242's fix
    would be COSMETIC and the spec must say so in those words. If the raw
    payload survives unchanged, the loss measured in P1/P2 above is proven
    to originate ENTIRELY in this library's own .strip() calls, and
    removing them is a real fix.
    """
    from SIL.LCModel.Core.Text import TsStringUtils

    project = target_sandbox
    text = project.Texts.Create(f"{TEST_PREFIX}p3_text")
    ws = project.project.DefaultVernWs

    results = {}
    for label, raw in PAYLOADS:
        para, seed_exc = _safe(lambda: project.Paragraphs.Create(text, "placeholder."), f"P3 seed para({label!r})")
        assert para is not None, f"Could not seed paragraph for {label!r}: {seed_exc}"

        def _bypass_write(raw=raw, p=para):
            with project.Transaction(f"P3 bypass {label}"):
                ts = TsStringUtils.MakeString(raw, ws)
                p.Contents = ts

        _, write_exc = _safe(_bypass_write, f"P3 bypass write({label!r})")

        reread = project.Paragraphs.GetText(para) if write_exc is None else None
        match = reread == raw
        results[label] = {"raw": raw, "reread": reread, "match": match, "write_exc": write_exc}
        print(
            f"[TABLE][P3] {label!r}: raw={raw!r} bypass_reread={reread!r} "
            f"EXACT_MATCH={match} write_exc={write_exc!r}"
        )

    survived = [label for label, row in results.items() if row["match"]]
    lost = [label for label, row in results.items() if not row["match"]]
    print(f"[SUMMARY][P3] payloads surviving the LCM bypass UNCHANGED: {survived}")
    print(f"[SUMMARY][P3] payloads altered even bypassing this library's own .strip(): {lost}")
    if not lost:
        print(
            "[VERDICT][P3] Whitespace survives layer B for EVERY payload -- the "
            "loss measured at layer A is caused ENTIRELY by this library's own "
            ".strip() calls; removing them is a REAL fix, not cosmetic."
        )
    else:
        print(
            f"[VERDICT][P3] {lost} were altered even when this library's own "
            ".strip() calls were bypassed entirely -- for those payloads, "
            "#242's fix would be COSMETIC: the LCM/FLEx layer itself "
            "normalises them regardless of what this library does."
        )

    # No blanket assertion on `match` -- that IS the open question this
    # probe exists to answer. Sanity-only: every bypass write reached the
    # LCM without raising.
    for label, row in results.items():
        assert row["write_exc"] is None, f"Bypass write for {label!r} raised: {row['write_exc']}"


# ===========================================================================
# P-4 -- IN-MEMORY vs ON-DISK
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p4_inmemory_vs_ondisk_persistence(target_sandbox_path):
    """
    Read back in-session, then CLOSE and REOPEN the same sandbox .fwdata
    and read again. Item 1 of this campaign was decided by these two
    differing -- do not assume they agree here.

    Uses the layer-B bypass (raw, unstripped MakeString) so this isolates
    whether ON-DISK persistence itself normalises whitespace, independent
    of anything this library's writers do.
    """
    from SIL.LCModel.Core.Text import TsStringUtils

    from flexicon.code.FLExProject import FLExProject

    fwdata_path = pathlib.Path(target_sandbox_path)

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    guids = {}
    inmemory = {}
    close_exc = None
    try:
        ws = project.project.DefaultVernWs
        text = project.Texts.Create(f"{TEST_PREFIX}p4_text")

        for label, raw in PAYLOADS:
            para, seed_exc = _safe(lambda: project.Paragraphs.Create(text, "placeholder."), f"P4 seed para({label!r})")
            assert para is not None, f"Could not seed paragraph for {label!r}: {seed_exc}"

            def _bypass_write(raw=raw, p=para):
                with project.Transaction(f"P4 bypass {label}"):
                    ts = TsStringUtils.MakeString(raw, ws)
                    p.Contents = ts

            _, write_exc = _safe(_bypass_write, f"P4 bypass write({label!r})")
            assert write_exc is None, f"Bypass write for {label!r} raised: {write_exc}"

            guids[label] = str(para.Guid)
            inmemory[label] = project.Paragraphs.GetText(para)
            print(f"[TABLE][P4][in-memory] {label!r}: raw={raw!r} inmemory={inmemory[label]!r}")

        _, close_exc = _safe(project.CloseProject, "P4 CloseProject")
    finally:
        _dispose_if_open(project, "P4 session1")

    assert close_exc is None, f"CloseProject() raised: {close_exc}"

    reopen = FLExProject()
    reopen.OpenProject(str(fwdata_path), writeEnabled=False)
    ondisk = {}
    try:
        for label, guid in guids.items():
            obj, obj_exc = _safe(lambda g=guid: reopen.Object(g), f"P4 reopen Object({label!r})")
            if obj is None:
                ondisk[label] = f"EXC:{obj_exc}"
                continue
            ondisk[label] = reopen.Paragraphs.GetText(obj)
            print(f"[TABLE][P4][on-disk]    {label!r}: ondisk={ondisk[label]!r}")
    finally:
        _safe(reopen.CloseProject, "P4 reopen CloseProject")
        _dispose_if_open(reopen, "P4 reopen")

    agree = {label: (inmemory[label] == ondisk.get(label)) for label in inmemory}
    disagreements = {label: (inmemory[label], ondisk.get(label)) for label, ok in agree.items() if not ok}
    print(f"[SUMMARY][P4] in-memory vs on-disk agreement per payload: {agree}")
    if disagreements:
        print(
            f"[VERDICT][P4] IN-MEMORY AND ON-DISK DISAGREE for: {disagreements} -- "
            "do not assume a value read before CloseProject() reflects what a "
            "user reopening the project will actually see."
        )
    else:
        print("[VERDICT][P4] in-memory and on-disk agree for every payload measured here.")

    # No blanket equality assertion -- that IS the open question. Sanity-only:
    # every payload was read back on both sides.
    assert set(inmemory) == {label for label, _ in PAYLOADS}
    assert set(ondisk) == {label for label, _ in PAYLOADS}


# ===========================================================================
# P-5 -- THE NON-STR BRANCH DIVERGENCE
# ===========================================================================

@pytest.mark.live_phase("ParagraphOperations", "add")
def test_p5_non_str_branch_divergence(target_sandbox):
    """
    ParagraphOperations (Create/SetText/InsertAt) does NOT strip the
    non-str branch:
        content_str = content.strip() if isinstance(content, str) else str(content)
    SegmentOperations.AppendSentence DOES strip it regardless of type:
        text_str = text.strip() if isinstance(text, str) else str(text).strip()

    Pass the SAME non-str object (str() == "ka ", trailing space) to a
    ParagraphOperations writer and to AppendSentence, and show whether they
    disagree as the source reads.
    """
    project = target_sandbox
    text = project.Texts.Create(f"{TEST_PREFIX}p5_text")
    payload = _NonStrPayload()

    para, create_exc = _safe(lambda: project.Paragraphs.Create(text, payload), "P5 Create(non-str)")
    assert create_exc is None, f"Create(non-str) raised: {create_exc}"
    para_read = project.Paragraphs.GetText(para)
    print(f"[TABLE][P5] ParagraphOperations.Create(non-str, str()={str(payload)!r}) -> {para_read!r}")

    seed, seed_exc = _safe(lambda: project.Paragraphs.Create(text, "Seed."), "P5 seed para")
    assert seed is not None, f"Seed paragraph creation failed: {seed_exc}"
    seg, append_exc = _safe(lambda: project.Segments.AppendSentence(seed, payload), "P5 AppendSentence(non-str)")
    assert append_exc is None, f"AppendSentence(non-str) raised: {append_exc}"
    seg_full = project.Paragraphs.GetText(seed)
    baseline, baseline_exc = _safe(lambda: project.Segments.GetBaselineText(seg), "P5 GetBaselineText(non-str)")
    print(
        f"[TABLE][P5] SegmentOperations.AppendSentence(non-str, str()={str(payload)!r}) -> "
        f"full_contents={seg_full!r} baseline={baseline!r} baseline_exc={baseline_exc!r}"
    )

    para_preserved_trailing_space = para_read.endswith("ka ")
    segment_preserved_trailing_space = seg_full.endswith("ka ")
    print(
        f"[SUMMARY][P5] ParagraphOperations preserved the non-str trailing space: "
        f"{para_preserved_trailing_space}. SegmentOperations.AppendSentence "
        f"preserved it: {segment_preserved_trailing_space}."
    )
    if para_preserved_trailing_space != segment_preserved_trailing_space:
        print(
            "[VERDICT][P5] CONFIRMED DIVERGENCE: the two writer families "
            "disagree on the SAME non-str input purely because of the "
            "isinstance(..., str) branch shape of their stripping lines."
        )
    else:
        print(
            "[VERDICT][P5] NO divergence measured for this input -- both "
            "families agree despite the source-level asymmetry."
        )

    # Sanity only: both writers actually produced content containing "ka".
    assert "ka" in para_read
    assert "ka" in seg_full
