#
#   test_issue242_whitespace_probe.py
#
#   CHECKPOINT 1 probe for issue #242 (specs/242-paragraph-whitespace):
#   measures whether whitespace written through the paragraph/segment text
#   writers actually survives a write-read cycle.
#
#   CHECKPOINT 3 UPDATE (2026-09-07): the fix ruled on by /lex-lead has now
#   LANDED at all four sites. Each site's .strip() is now a THROWAWAY used
#   only for the emptiness check; the caller's ORIGINAL payload reaches
#   TsStringUtils.MakeString unmodified. test_p1/p2/p3/p4/p5 below are
#   FLIPPED from asserting/observing "stripped" (pre-fix) to asserting
#   "preserved" (post-fix); the pre-fix behaviour is kept in comments for
#   the historical record. test_p6 through test_p8 are NEW additions for
#   Checkpoint 3 (see specs/242-paragraph-whitespace/evidence/
#   live-t1-t2-fix.md for the PREDICTIONS committed before this run).
#
#   THE FOUR SITES UNDER STUDY (post-fix line numbers; see
#   `git diff --stat -- flexicon/` for the exact patch):
#     flexicon/code/TextsWords/ParagraphOperations.py       Create
#     flexicon/code/TextsWords/ParagraphOperations.py       SetText
#     flexicon/code/TextsWords/ParagraphOperations.py       InsertAt
#     flexicon/code/TextsWords/SegmentOperations.py         AppendSentence
#   PRE-FIX (historical record): all four stripped a copy of the incoming
#   text for the emptiness check and then persisted the STRIPPED value via
#   TsStringUtils.MakeString. Branch asymmetry found by inspection:
#   ParagraphOperations did NOT strip the non-str branch (`str(content)`),
#   while SegmentOperations DID strip it (`str(text).strip()`) -- see
#   test_p5 below. POST-FIX: that asymmetry is resolved -- neither family
#   strips the non-str branch any more (SegmentOperations's trailing
#   `.strip()` on `str(text)` was deliberately removed per the ruling).
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
    POST-FIX BEHAVIOUR (layer A): call Create / SetText / InsertAt as they
    ship after the Checkpoint 3 fix, for every payload in the matrix, and
    re-read via GetText(). The .strip() at each site is now a THROWAWAY
    used only for the emptiness check; the persisted value is the raw,
    UNSTRIPPED payload. So each writer's re-read value is predicted to
    equal `raw` byte-for-byte (P6), not `raw.strip()`.

    HISTORICAL RECORD (pre-fix, cycle 1): all three writers shared one
    stripping line:
        content_str = content.strip() if isinstance(content, str) else str(content)
    and persisted the STRIPPED value, so the pre-fix re-read equalled
    `raw.strip()` for every payload, not `raw`.
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

    # P6: post-fix, each writer must round-trip the RAW payload
    # byte-for-byte (not `raw.strip()`). This is the headline assertion
    # this test flipped from "stripped" to "preserved" for.
    for label, row in results.items():
        assert row["create_exc"] is None and row["insert_exc"] is None and row["settext_exc"] is None, (
            f"Payload {label!r}: unexpected exception -- {row}"
        )
        assert row["create"] == row["insert"] == row["settext"] == row["raw"], (
            f"Payload {label!r} (raw={row['raw']!r}): expected Create/InsertAt/"
            f"SetText to all round-trip the RAW payload post-fix -- got "
            f"{row['create']!r} / {row['insert']!r} / {row['settext']!r}. "
            f"(Pre-fix, cycle 1, these would have equalled raw.strip().)"
        )


# ===========================================================================
# P-2 -- LAYER A: AppendSentence (SegmentOperations)
# ===========================================================================

@pytest.mark.live_phase("SegmentOperations", "add")
def test_p2_layer_a_append_sentence_matrix(target_sandbox):
    """
    POST-FIX BEHAVIOUR (layer A) for AppendSentence. Checkpoint 3 landed:
        text_str = text if isinstance(text, str) else str(text)
        if not text_str.strip():
            raise FP_ParameterError("text cannot be empty")
    so text_str is now the RAW payload; the .strip() is a throwaway used
    only for the emptiness check (the non-str branch's former trailing
    `.strip()` was also removed, per the ruling).

    HISTORICAL RECORD (pre-fix, cycle 1): the stripping line was
        text_str = text.strip() if isinstance(text, str) else str(text).strip()
    and AppendSentence persisted the STRIPPED value.

    Each payload gets a FRESH paragraph seeded with "Seed." so the append
    takes AppendSentence's "already terminated" branch (a single space
    separator is inserted, not ". "). Both of AppendSentence's branches
    consume the SAME `text_str`, so exercising one branch is sufficient to
    characterise the strip itself; the current_length == 0 (empty-
    paragraph, direct-write) branch was NOT separately probed here --
    noted explicitly rather than silently skipped. Post-fix, full_contents
    is predicted to equal "Seed. " + raw exactly (P6).

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

    # P6: post-fix, AppendSentence must persist the RAW payload
    # byte-for-byte. The seed paragraph ("Seed.") already ends in ".", so
    # AppendSentence takes the "already terminated" branch and inserts a
    # single space separator before the appended text.
    for label, row in results.items():
        expected = f"Seed. {row['raw']}"
        assert row["full_contents"] == expected, (
            f"Payload {label!r} (raw={row['raw']!r}): expected full_contents "
            f"to round-trip the RAW payload post-fix -- expected "
            f"{expected!r}, got {row['full_contents']!r}. (Pre-fix, cycle 1, "
            f"this would have equalled 'Seed. ' + raw.strip().)"
        )

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

    CHECKPOINT 1 (cycle 1) answered this as an open question, recorded as
    contract item C3(i): whitespace survives a raw `MakeString` write for
    every payload in the matrix -- the loss measured at layer A (P1/P2)
    originates ENTIRELY in this library's own .strip() calls, not the LCM/
    FLEx layer. CHECKPOINT 3 FLIPS the observational-only verdict below
    into a hard assertion (`match` for every payload), locking in that
    answer as a regression test now that the fix at layer A depends on it.

    HISTORICAL RECORD (pre-fix, cycle 1): no blanket assertion on `match`
    existed here -- it was "the open question this probe exists to
    answer," reported via [VERDICT] prints only.
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

    # P6 (flipped from an open question to a hard assertion, Checkpoint 3):
    # every payload must survive the raw LCM bypass unchanged.
    for label, row in results.items():
        assert row["write_exc"] is None, f"Bypass write for {label!r} raised: {row['write_exc']}"
        assert row["match"], (
            f"Payload {label!r} (raw={row['raw']!r}): expected the raw LCM "
            f"bypass to round-trip unchanged -- got {row['reread']!r}. "
            f"(This was the open question in cycle 1; C3(i) already "
            f"answered it as 'yes, for every payload'.)"
        )


# ===========================================================================
# P-4 -- IN-MEMORY vs ON-DISK
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p4_inmemory_vs_ondisk_persistence(target_sandbox_path):
    """
    Read back in-session, then CLOSE and REOPEN the same sandbox .fwdata
    and read again.

    Uses the layer-B bypass (raw, unstripped MakeString) so this isolates
    whether ON-DISK persistence itself normalises whitespace, independent
    of anything this library's writers do. CHECKPOINT 3 FLIPS this from an
    open question into a hard assertion: both in-memory and on-disk reads
    must equal the RAW payload for every entry in the matrix (P6).

    HISTORICAL RECORD (pre-fix, cycle 1): no blanket equality assertion
    existed here -- "Item 1 of this campaign was decided by these two
    differing -- do not assume they agree here" was the operative caution,
    and in-memory/on-disk agreement (or disagreement) was reported via
    [VERDICT] prints only.
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

    # P6 (flipped from an open question to a hard assertion, Checkpoint 3):
    # both in-memory and on-disk reads must equal the RAW payload.
    assert set(inmemory) == {label for label, _ in PAYLOADS}
    assert set(ondisk) == {label for label, _ in PAYLOADS}
    for label, raw in PAYLOADS:
        assert inmemory[label] == raw, (
            f"Payload {label!r}: expected in-memory read to equal raw "
            f"{raw!r}, got {inmemory[label]!r}"
        )
        assert ondisk[label] == raw, (
            f"Payload {label!r}: expected on-disk read (after close+reopen) "
            f"to equal raw {raw!r}, got {ondisk[label]!r}"
        )


# ===========================================================================
# P-5 -- THE NON-STR BRANCH DIVERGENCE
# ===========================================================================

@pytest.mark.live_phase("ParagraphOperations", "add")
def test_p5_non_str_branch_divergence(target_sandbox):
    """
    POST-FIX (Checkpoint 3): the C6 non-str-branch asymmetry is RESOLVED.
    Neither family strips the non-str branch any more:
        ParagraphOperations: content_str = content if isinstance(content, str) else str(content)
        SegmentOperations:   text_str = text if isinstance(text, str) else str(text)
    (SegmentOperations's former trailing `.strip()` on `str(text)` was
    deliberately removed per the ruling.) Both are therefore predicted to
    PRESERVE the trailing space on the same non-str payload.

    HISTORICAL RECORD (pre-fix, cycle 1): ParagraphOperations did NOT
    strip the non-str branch (`str(content)`), while SegmentOperations DID
    strip it (`str(text).strip()`) -- confirmed as a divergence for this
    exact payload.

    Pass the SAME non-str object (str() == "ka ", trailing space) to a
    ParagraphOperations writer and to AppendSentence, and confirm they now
    AGREE (both preserve it).
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

    # P6 (flipped, Checkpoint 3): the C6 asymmetry is resolved -- both
    # families must now preserve the non-str trailing space, and agree
    # with each other. (Pre-fix, cycle 1: para_preserved_trailing_space was
    # True and segment_preserved_trailing_space was False -- a confirmed
    # divergence.)
    assert para_preserved_trailing_space, (
        f"Expected ParagraphOperations.Create(non-str) to preserve the "
        f"trailing space post-fix -- got {para_read!r}"
    )
    assert segment_preserved_trailing_space, (
        f"Expected SegmentOperations.AppendSentence(non-str) to preserve "
        f"the trailing space post-fix -- got {seg_full!r}"
    )
    assert para_preserved_trailing_space == segment_preserved_trailing_space, (
        "Expected the C6 asymmetry to be resolved: both writer families "
        "must agree on the same non-str input."
    )

    # Sanity only: both writers actually produced content containing "ka".
    assert "ka" in para_read
    assert "ka" in seg_full


# ===========================================================================
# P-7 -- WHITESPACE-ONLY INPUT STILL RAISES (NEW, Checkpoint 3)
# ===========================================================================

@pytest.mark.live_phase("ParagraphOperations", "add")
def test_p7_whitespace_only_still_raises(target_sandbox):
    """
    P7: the fix uses `.strip()` as a THROWAWAY for the emptiness check
    only -- it must still catch a whitespace-only payload as empty, at all
    four sites. Persisting the raw payload does NOT mean persisting
    "nothing but whitespace" silently succeeds.
    """
    project = target_sandbox
    text = project.Texts.Create(f"{TEST_PREFIX}p7_text")
    whitespace_only = "   "

    # Site 1: Create
    _, create_exc = _safe(
        lambda: project.Paragraphs.Create(text, whitespace_only), "P7 Create(whitespace-only)"
    )
    print(f"[TABLE][P7] Create(whitespace-only={whitespace_only!r}) -> raised {create_exc!r}")
    assert create_exc is not None and create_exc.startswith("FP_ParameterError"), (
        f"Expected Create(whitespace-only) to raise FP_ParameterError -- got {create_exc!r}"
    )

    # Site 2: SetText (needs a valid seed paragraph first)
    seed, seed_exc = _safe(lambda: project.Paragraphs.Create(text, "Seed."), "P7 seed para")
    assert seed is not None, f"Seed paragraph creation failed: {seed_exc}"
    _, settext_exc = _safe(
        lambda: project.Paragraphs.SetText(seed, whitespace_only), "P7 SetText(whitespace-only)"
    )
    print(f"[TABLE][P7] SetText(whitespace-only={whitespace_only!r}) -> raised {settext_exc!r}")
    assert settext_exc is not None and settext_exc.startswith("FP_ParameterError"), (
        f"Expected SetText(whitespace-only) to raise FP_ParameterError -- got {settext_exc!r}"
    )
    # Confirm SetText did not silently write the whitespace-only payload.
    assert project.Paragraphs.GetText(seed) == "Seed.", (
        "SetText(whitespace-only) raised, but the seed paragraph's content "
        "changed anyway -- the raise must happen BEFORE any write."
    )

    # Site 3: InsertAt
    para_count = text.ContentsOA.ParagraphsOS.Count
    _, insert_exc = _safe(
        lambda: project.Paragraphs.InsertAt(text, para_count, whitespace_only),
        "P7 InsertAt(whitespace-only)",
    )
    print(f"[TABLE][P7] InsertAt(whitespace-only={whitespace_only!r}) -> raised {insert_exc!r}")
    assert insert_exc is not None and insert_exc.startswith("FP_ParameterError"), (
        f"Expected InsertAt(whitespace-only) to raise FP_ParameterError -- got {insert_exc!r}"
    )

    # Site 4: AppendSentence
    seed2, seed2_exc = _safe(lambda: project.Paragraphs.Create(text, "Seed2."), "P7 seed2 para")
    assert seed2 is not None, f"Seed2 paragraph creation failed: {seed2_exc}"
    _, append_exc = _safe(
        lambda: project.Segments.AppendSentence(seed2, whitespace_only),
        "P7 AppendSentence(whitespace-only)",
    )
    print(f"[TABLE][P7] AppendSentence(whitespace-only={whitespace_only!r}) -> raised {append_exc!r}")
    assert append_exc is not None and append_exc.startswith("FP_ParameterError"), (
        f"Expected AppendSentence(whitespace-only) to raise FP_ParameterError -- got {append_exc!r}"
    )
    assert project.Paragraphs.GetText(seed2) == "Seed2.", (
        "AppendSentence(whitespace-only) raised, but the seed paragraph's "
        "content changed anyway -- the raise must happen BEFORE any write."
    )

    print(
        "[VERDICT][P7] whitespace-only input still raises FP_ParameterError at all "
        "four sites, confirming the .strip() emptiness check survived the fix "
        "as a throwaway check (it just no longer affects what gets persisted "
        "for non-empty payloads)."
    )


# ===========================================================================
# P-8 -- MEASURE (DO NOT FIX): TERMINATOR BRANCH READS THE RAW LAST CHAR
# ===========================================================================

@pytest.mark.live_phase("SegmentOperations", "add")
def test_p8_terminator_branch_reads_raw_trailing_space(target_sandbox):
    """
    P8: MEASURE ONLY, per the ruling -- do not fix, report it.

    AppendSentence's terminator branch (SegmentOperations.py, untouched by
    this fix) reads the RAW last character of para.Contents to decide
    whether the paragraph is already sentence-terminated. Before this fix,
    a paragraph's Contents could not end in a literal trailing space
    (Create/SetText/InsertAt all stripped it). After this fix, they no
    longer strip, so a paragraph can now genuinely end in " ".

    PREDICTION (P8, committed before this run in
    evidence/live-t1-t2-fix.md): create a paragraph via
    Paragraphs.Create() with content "foo " (trailing space, now
    preserved). Append "bar" via AppendSentence. The terminator branch
    reads the last char as " ", which is NOT in (".", "!", "?"), so it
    takes the "insert '. ' as sentence terminator" branch -- producing
    "foo . bar" (a space BEFORE the period), a state that was UNREACHABLE
    before this fix (because Contents could never end in a raw space).

    This test measures and asserts the PREDICTED (if anomalous) behaviour
    to lock it in as a regression-detectable fact. It does NOT change
    SegmentOperations.py's terminator logic (lines left untouched per the
    ruling). /lex-lead rules on whether this is acceptable next cycle.
    """
    project = target_sandbox
    text = project.Texts.Create(f"{TEST_PREFIX}p8_text")

    para, create_exc = _safe(
        lambda: project.Paragraphs.Create(text, "foo "), "P8 Create('foo ', trailing space)"
    )
    assert create_exc is None, f"Create('foo ') raised: {create_exc}"
    pre_append = project.Paragraphs.GetText(para)
    print(f"[TABLE][P8] pre-append Contents: {pre_append!r}")
    assert pre_append == "foo ", (
        f"Precondition failed: expected the seed paragraph to end in a raw "
        f"trailing space post-fix -- got {pre_append!r}"
    )

    _, append_exc = _safe(
        lambda: project.Segments.AppendSentence(para, "bar"), "P8 AppendSentence('bar')"
    )
    assert append_exc is None, f"AppendSentence('bar') raised: {append_exc}"

    post_append = project.Paragraphs.GetText(para)
    print(f"[TABLE][P8] post-append Contents: {post_append!r}")

    predicted = "foo . bar"
    if post_append == predicted:
        print(
            f"[VERDICT][P8] CONFIRMED: terminator branch read the raw trailing "
            f"space as the last char (not in '.!?'), inserting '. ' and "
            f"producing {post_append!r} -- a space-before-period state that "
            f"was UNREACHABLE before this fix. NOT FIXED here per the ruling; "
            f"/lex-lead rules on it next cycle."
        )
    else:
        print(
            f"[VERDICT][P8] PREDICTION MISS: expected {predicted!r}, got "
            f"{post_append!r}. Reporting the actual measured value, not "
            f"adjusting the prediction after the fact."
        )

    assert post_append == predicted, (
        f"P8 measurement: expected {predicted!r} (the predicted anomaly), "
        f"got {post_append!r}. This assertion locks in the MEASURED "
        f"behaviour so a future change to the terminator logic shows up "
        f"here as a diff, not a silent regression."
    )
