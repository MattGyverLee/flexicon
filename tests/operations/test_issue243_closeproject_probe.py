#
#   test_issue243_closeproject_probe.py
#
#   CHECKPOINT 1 probe for issue #243 (specs/243-closeproject-save-guard):
#   `FLExProject.CloseProject()` (FLExProject.py:318-338) calls
#   `MainCacheAccessor.EndNonUndoableTask()` (the "End mirror" for the
#   session-long `BeginNonUndoableTask()` envelope opened at `OpenProject()`
#   under `undoable=False`) BEFORE `usm.Save()`, with no guard between them.
#   If the End mirror raises, `usm.Save()` never runs and the whole
#   session's uncommitted work is lost.
#
#   This file measures the bug; it does NOT fix it. No file under
#   flexicon/code/ is touched by this task.
#
#   Structure copied from tests/operations/test_target_live_smoke.py (the
#   canonical template) and tests/operations/test_issue254_morphra_probe.py
#   (the investigation-probe convention: print findings, assert only on
#   setup sanity and on the headline claims).
#
#   Uses target_sandbox_path (tests/conftest.py) exclusively for the P-3/
#   P-4/P-5 probes: those need to OPEN, CLOSE, and REOPEN the same .fwdata
#   file within a single test, which the auto-opening sandbox fixtures
#   cannot express. Every project opened in this file is disposed in a
#   `finally:` block -- CloseProject() itself does NOT dispose when the
#   line-326 mirror raises (the raise propagates before reaching
#   `self.project.Dispose()` at FLExProject.py:334), so leaving that to
#   CloseProject() alone would leak the file lock and break the reopen
#   half of the probe.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import pathlib

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"
N_ENTRIES = 25


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


def _depth(project):
    return project.project.ActionHandlerAccessor.CurrentDepth


def _dispose_if_open(project, label):
    """
    Manually dispose the LCM cache if CloseProject() did not reach its own
    Dispose() call (i.e. it raised before FLExProject.py:334). Idempotent:
    safe to call even if CloseProject() already succeeded.
    """
    if hasattr(project, "project"):
        try:
            project.project.Dispose()
            del project.project
            print(f"[PROBE] {label}: manually disposed cache (CloseProject did not reach its own Dispose)")
        except Exception as exc:
            print(f"[PROBE] {label}: manual dispose also raised: {type(exc).__name__}: {exc}")


def _create_test_entries(project, prefix, n):
    created = []
    for i in range(n):
        name = f"{prefix}{i:03d}"
        entry = project.LexEntry.Create(name)
        created.append(name)
    return created


def _count_prefixed_entries(project, prefix):
    count = 0
    for entry in project.LexEntry.GetAll():
        form = project.LexEntry.GetLexemeForm(entry)
        if form and form.startswith(prefix):
            count += 1
    return count


# ===========================================================================
# P-1 -- MODE MATRIX
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "read")
def test_p1_mode_matrix(target_sandbox_path):
    """
    For each of (a) writeEnabled=True, undoable=True (4.4.0 default),
    (b) writeEnabled=True, undoable=False, (c) writeEnabled=False: record
    writeEnabled/_undoable and whether line 326's guard
    (`if self.writeEnabled: if not self._undoable:`) is reached.
    """
    from flexicon.code.FLExProject import FLExProject

    results = {}

    # --- Mode (a): default undoable=True ---
    project = FLExProject()
    project.OpenProject(str(target_sandbox_path), writeEnabled=True)
    try:
        we, undo = project.writeEnabled, project._undoable
        reached = we and not undo
        results["a_default_4.4.0"] = (we, undo, reached)
        print(f"[PROBE][P1] mode a (writeEnabled=True, undoable=default): writeEnabled={we} _undoable={undo} line326_reached={reached}")
    finally:
        _safe(project.CloseProject, "P1 mode a CloseProject")
        _dispose_if_open(project, "P1 mode a")

    # --- Mode (b): writeEnabled=True, undoable=False ---
    project = FLExProject()
    project.OpenProject(str(target_sandbox_path), writeEnabled=True, undoable=False)
    try:
        we, undo = project.writeEnabled, project._undoable
        reached = we and not undo
        results["b_undoable_false"] = (we, undo, reached)
        print(f"[PROBE][P1] mode b (writeEnabled=True, undoable=False): writeEnabled={we} _undoable={undo} line326_reached={reached}")
    finally:
        _safe(project.CloseProject, "P1 mode b CloseProject")
        _dispose_if_open(project, "P1 mode b")

    # --- Mode (c): writeEnabled=False ---
    project = FLExProject()
    project.OpenProject(str(target_sandbox_path), writeEnabled=False)
    try:
        we, undo = project.writeEnabled, project._undoable
        reached = we and not undo
        results["c_readonly"] = (we, undo, reached)
        print(f"[PROBE][P1] mode c (writeEnabled=False): writeEnabled={we} _undoable={undo} line326_reached={reached}")
    finally:
        _safe(project.CloseProject, "P1 mode c CloseProject")
        _dispose_if_open(project, "P1 mode c")

    print(f"[PROBE][P1] full matrix: {results}")

    assert results["a_default_4.4.0"] == (True, True, False)
    assert results["b_undoable_false"] == (True, False, True)
    assert results["c_readonly"] == (False, False, False)

    only_b_reaches = (
        results["b_undoable_false"][2] is True
        and results["a_default_4.4.0"][2] is False
        and results["c_readonly"][2] is False
    )
    print(f"[PROBE][P1] CONFIRMED: line 326 reachable ONLY in mode (b): {only_b_reaches}")
    assert only_b_reaches


# ===========================================================================
# P-2 -- DEPTH TABLE
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p2_depth_table(target_sandbox_path):
    """
    Record project.project.ActionHandlerAccessor.CurrentDepth at each of
    the requested moments, across both write modes and a read-only open.
    """
    from flexicon.code.FLExProject import FLExProject

    depths = {}

    # --- Session 1: undoable=False ---
    project = FLExProject()
    project.OpenProject(str(target_sandbox_path), writeEnabled=True, undoable=False)
    try:
        depths["open_undoable_false"] = _depth(project)
        print(f"[PROBE][P2] after OpenProject(undoable=False): CurrentDepth={depths['open_undoable_false']}")

        with project.Transaction("probe"):
            depths["transaction_block_undoable_false"] = _depth(project)
            print(f"[PROBE][P2] inside Transaction() block, undoable=False: CurrentDepth={depths['transaction_block_undoable_false']}")

        aborted = project.AbortSession()
        depths["after_abort_session_true"] = _depth(project)
        print(f"[PROBE][P2] AbortSession() returned {aborted}; CurrentDepth={depths['after_abort_session_true']}")

        project.project.MainCacheAccessor.EndNonUndoableTask()
        depths["after_manual_end_nonundoable_task"] = _depth(project)
        print(f"[PROBE][P2] after manual EndNonUndoableTask(): CurrentDepth={depths['after_manual_end_nonundoable_task']}")

        # Repair the envelope so this session can close cleanly without
        # tripping the very bug under study -- P-2 is a depth-table probe,
        # not a P-3/P-4/P-5 reproduction.
        _safe(project.project.MainCacheAccessor.BeginNonUndoableTask, "P2 repair BeginNonUndoableTask")
    finally:
        _safe(project.CloseProject, "P2 session1 CloseProject")
        _dispose_if_open(project, "P2 session1")

    # --- Session 2: undoable=True ---
    project = FLExProject()
    project.OpenProject(str(target_sandbox_path), writeEnabled=True, undoable=True)
    try:
        depths["open_undoable_true"] = _depth(project)
        print(f"[PROBE][P2] after OpenProject(undoable=True): CurrentDepth={depths['open_undoable_true']}")

        with project.Transaction("probe"):
            depths["transaction_block_undoable_true"] = _depth(project)
            print(f"[PROBE][P2] inside Transaction() block, undoable=True: CurrentDepth={depths['transaction_block_undoable_true']}")

        with project.UndoableOperation("probe"):
            depths["undoable_operation_block"] = _depth(project)
            print(f"[PROBE][P2] inside UndoableOperation() block, undoable=True: CurrentDepth={depths['undoable_operation_block']}")
    finally:
        _safe(project.CloseProject, "P2 session2 CloseProject")
        _dispose_if_open(project, "P2 session2")

    # --- Session 3: read-only ---
    project = FLExProject()
    project.OpenProject(str(target_sandbox_path), writeEnabled=False)
    try:
        depth_or_exc, exc_msg = _safe(lambda: _depth(project), "P2 read-only CurrentDepth")
        depths["readonly_current_depth"] = depth_or_exc if exc_msg is None else f"EXC:{exc_msg}"
        print(f"[PROBE][P2] read-only project CurrentDepth read result: {depths['readonly_current_depth']}")
    finally:
        _safe(project.CloseProject, "P2 session3 CloseProject")
        _dispose_if_open(project, "P2 session3")

    print(f"[PROBE][P2] full depth table: {depths}")

    # Setup sanity only -- the exploratory readings above are the payload
    # for the evidence file, not pass/fail gates.
    assert depths["open_undoable_false"] in (0, 1)
    assert depths["open_undoable_true"] in (0, 1)


# ===========================================================================
# P-3 (+ P-6) -- THE P0 REPRODUCTION, FULLY LIVE
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p3_p6_reproduction_and_symptom(target_sandbox_path, capsys):
    """
    Force the End mirror at FLExProject.py:326 to have nothing to end by
    calling EndNonUndoableTask() manually before CloseProject(). Capture
    the resulting exception, then reopen the same .fwdata read-only and
    count the TEST_ entries created before the forced failure. Also folds
    in P-6: file size before/after, any new sibling files, and a search
    for the literal text "Commit at wrong place." in whatever was raised
    or printed.
    """
    from flexicon.code.FLExProject import FLExProject

    fwdata_path = pathlib.Path(target_sandbox_path)
    sandbox_dir = fwdata_path.parent
    prefix = f"{TEST_PREFIX}p3_"

    size_before = os.path.getsize(fwdata_path)
    dir_listing_before = sorted(p.name for p in sandbox_dir.iterdir())
    print(f"[PROBE][P6] .fwdata size before run: {size_before} bytes")
    print(f"[PROBE][P6] sandbox dir listing before run: {dir_listing_before}")

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    close_exc_msg = None
    try:
        created = _create_test_entries(project, prefix, N_ENTRIES)
        print(f"[PROBE][P3] created {len(created)} entries with prefix {prefix!r}")

        # Force the End mirror to have nothing to end: end the session
        # envelope manually, ONCE, leaving CloseProject()'s own
        # EndNonUndoableTask() call at line 326 with no task open.
        _safe(project.project.MainCacheAccessor.EndNonUndoableTask, "P3 manual EndNonUndoableTask")

        _, close_exc_msg = _safe(project.CloseProject, "P3 CloseProject (expected to raise)")
    finally:
        # CloseProject() raising at line 326 means it never reaches its own
        # Dispose() call at line 334 -- dispose manually so the file lock
        # is released and the reopen below can succeed.
        _dispose_if_open(project, "P3")

    captured = capsys.readouterr()
    size_after = os.path.getsize(fwdata_path)
    dir_listing_after = sorted(p.name for p in sandbox_dir.iterdir())
    new_siblings = sorted(set(dir_listing_after) - set(dir_listing_before))

    # Re-print everything that was swallowed into the capsys buffer above
    # (capsys captures all stdout for the whole test once requested, even
    # under -s) so it is visible in the pytest -s transcript pasted into
    # the evidence file.
    print(f"[PROBE][P3] CloseProject() raised: {close_exc_msg}")
    print(f"[PROBE][P6] .fwdata size before run: {size_before} bytes")
    print(f"[PROBE][P6] sandbox dir listing before run: {dir_listing_before}")
    print(f"[PROBE][P6] .fwdata size after failed close: {size_after} bytes (delta={size_after - size_before})")
    print(f"[PROBE][P6] sandbox dir listing after run: {dir_listing_after}")
    print(f"[PROBE][P6] new sibling files that appeared: {new_siblings}")

    marker_in_exc = bool(close_exc_msg and "Commit at wrong place." in close_exc_msg)
    marker_in_stdout = "Commit at wrong place." in captured.out
    marker_in_stderr = "Commit at wrong place." in captured.err
    print(f"[PROBE][P6] 'Commit at wrong place.' found in CloseProject() exception message: {marker_in_exc}")
    print(f"[PROBE][P6] 'Commit at wrong place.' found in captured stdout: {marker_in_stdout}")
    print(f"[PROBE][P6] 'Commit at wrong place.' found in captured stderr: {marker_in_stderr}")

    assert close_exc_msg is not None, (
        "CloseProject() did not raise when the End mirror had nothing to "
        "end -- the P0 bug's forcing condition did not reproduce."
    )

    # Reopen the SAME .fwdata path read-only and count survivors.
    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        surviving_count = _count_prefixed_entries(reopen_project, prefix)
        print(f"[PROBE][P3] TEST_ entries surviving after failed CloseProject, re-read from LCM: {surviving_count} / {N_ENTRIES}")
    finally:
        _safe(reopen_project.CloseProject, "P3 reopen CloseProject")
        _dispose_if_open(reopen_project, "P3 reopen")

    print(f"[PROBE][P3] VERDICT: expected 0 survivors (total session loss); observed {surviving_count}")
    assert surviving_count == 0, (
        f"Expected total loss of the {N_ENTRIES}-entry session (0 survivors) "
        f"because the raise at line 326 skips the Save() at line 332, but "
        f"{surviving_count} entries survived."
    )


# ===========================================================================
# P-4 -- CONTROL RUN
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p4_control_run_normal_close(target_sandbox_path):
    """
    Identical flow to P-3 but WITHOUT the manual End -- CloseProject() runs
    normally. Proves the P-3 loss is caused by ordering, not by the sandbox.
    """
    from flexicon.code.FLExProject import FLExProject

    fwdata_path = pathlib.Path(target_sandbox_path)
    prefix = f"{TEST_PREFIX}p4_"

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    close_exc_msg = None
    try:
        created = _create_test_entries(project, prefix, N_ENTRIES)
        print(f"[PROBE][P4] created {len(created)} entries with prefix {prefix!r}")

        _, close_exc_msg = _safe(project.CloseProject, "P4 CloseProject (expected to succeed)")
    finally:
        _dispose_if_open(project, "P4")

    assert close_exc_msg is None, f"CloseProject() raised unexpectedly in the control run: {close_exc_msg}"

    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        surviving_count = _count_prefixed_entries(reopen_project, prefix)
        print(f"[PROBE][P4] TEST_ entries surviving after normal CloseProject, re-read from LCM: {surviving_count} / {N_ENTRIES}")
    finally:
        _safe(reopen_project.CloseProject, "P4 reopen CloseProject")
        _dispose_if_open(reopen_project, "P4 reopen")

    print(f"[PROBE][P4] VERDICT: expected {N_ENTRIES} survivors; observed {surviving_count}")
    assert surviving_count == N_ENTRIES, (
        f"Control run should persist all {N_ENTRIES} entries via the normal "
        f"CloseProject() path, but only {surviving_count} survived."
    )


# ===========================================================================
# P-5 -- THE GO/NO-GO FOR THE P0 FIX
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p5_save_before_forced_end(target_sandbox_path):
    """
    Does usm.Save() (via project.SaveChanges()) actually persist to disk
    while the non-undoable session envelope is still OPEN?

    Flow: open undoable=False, create N_ENTRIES TEST_ entries, call
    project.SaveChanges(), THEN force the failing End as in P-3, let
    CloseProject() raise, dispose, reopen, count.

    If the count is N_ENTRIES: save-before-end (reordering) is a valid fix
    shape. If it is 0, or SaveChanges() itself raises while depth > 0:
    reordering alone cannot fix this; the fix must be a try/finally around
    the End call instead.
    """
    from flexicon.code.FLExProject import FLExProject

    fwdata_path = pathlib.Path(target_sandbox_path)
    prefix = f"{TEST_PREFIX}p5_"

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    save_exc_msg = None
    close_exc_msg = None
    try:
        created = _create_test_entries(project, prefix, N_ENTRIES)
        print(f"[PROBE][P5] created {len(created)} entries with prefix {prefix!r}")

        depth_before_save = _depth(project)
        print(f"[PROBE][P5] CurrentDepth before SaveChanges(): {depth_before_save}")

        _, save_exc_msg = _safe(project.SaveChanges, "P5 SaveChanges() while envelope still open")

        depth_after_save = _safe(lambda: _depth(project), "P5 CurrentDepth after SaveChanges()")[0]
        print(f"[PROBE][P5] CurrentDepth after SaveChanges() attempt: {depth_after_save}")

        # THEN force the failing End as in P-3, regardless of whether
        # SaveChanges() itself raised -- the task asks for this exact
        # sequence so the final count answers the go/no-go question
        # unambiguously.
        _safe(project.project.MainCacheAccessor.EndNonUndoableTask, "P5 manual EndNonUndoableTask (post-SaveChanges)")

        _, close_exc_msg = _safe(project.CloseProject, "P5 CloseProject (expected to raise)")
    finally:
        _dispose_if_open(project, "P5")

    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        surviving_count = _count_prefixed_entries(reopen_project, prefix)
        print(f"[PROBE][P5] TEST_ entries surviving, re-read from LCM: {surviving_count} / {N_ENTRIES}")
    finally:
        _safe(reopen_project.CloseProject, "P5 reopen CloseProject")
        _dispose_if_open(reopen_project, "P5 reopen")

    if save_exc_msg is not None:
        verdict = (
            "SaveChanges() itself RAISED while depth > 0 "
            f"({save_exc_msg}). Reordering (Save-before-End) is NOT a "
            "viable fix shape by itself -- the fix must be a try/finally "
            "(or equivalent) around the End call instead."
        )
    elif surviving_count == N_ENTRIES:
        verdict = (
            "SaveChanges() succeeded while depth > 0 and all entries "
            "survived the forced End failure -- save-before-end (reordering) "
            "is a VALID fix shape."
        )
    else:
        verdict = (
            f"SaveChanges() did not raise but only {surviving_count}/{N_ENTRIES} "
            "entries survived -- reordering alone is NOT sufficient; "
            "investigate further before choosing a fix shape."
        )
    print(f"[PROBE][P5] GO/NO-GO VERDICT: {verdict}")

    # This is the headline evidence artifact for cycle 1 -- record it, do
    # not silently swallow an unexpected shape.
    assert save_exc_msg is not None or surviving_count in (0, N_ENTRIES), (
        "Unexpected partial-survival count -- neither of the two "
        "documented shapes (all-or-nothing) was observed: "
        f"surviving_count={surviving_count}"
    )
