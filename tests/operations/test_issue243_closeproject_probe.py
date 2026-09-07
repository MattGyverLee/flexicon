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
# T1 -- PUBLIC CurrentDepth / HasOpenSessionTask() SURFACE (spec.md C2-C5)
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p2_public_surface_matches_depth_table(target_sandbox_path):
    """
    Re-run the frozen P-2 depth-table moments (spec.md section 2), but read
    the NEW public `CurrentDepth` property / `HasOpenSessionTask()` method
    instead of the raw `_depth()` helper, and assert they agree with the
    frozen table row-by-row. Also covers the two new closed/never-opened
    raise cases (C4) that the original P-2 probe did not need: (a) after a
    successful CloseProject(), and (b) on a FLExProject() instance on which
    OpenProject() was never called.
    """
    from flexicon.code.FLExProject import FLExProject
    from flexicon.code.exceptions import FP_ProjectError

    rows = {}

    # --- Session 1: undoable=False ---
    project = FLExProject()
    project.OpenProject(str(target_sandbox_path), writeEnabled=True, undoable=False)
    try:
        rows["open_undoable_false"] = (project.CurrentDepth, project.HasOpenSessionTask())
        print(f"[PROBE][T1] after OpenProject(undoable=False): CurrentDepth={rows['open_undoable_false'][0]} HasOpenSessionTask={rows['open_undoable_false'][1]}")

        with project.Transaction("probe"):
            rows["transaction_block_undoable_false"] = (project.CurrentDepth, project.HasOpenSessionTask())
            print(f"[PROBE][T1] inside Transaction() block, undoable=False: CurrentDepth={rows['transaction_block_undoable_false'][0]} HasOpenSessionTask={rows['transaction_block_undoable_false'][1]}")

        aborted = project.AbortSession()
        rows["after_abort_session_true"] = (project.CurrentDepth, project.HasOpenSessionTask())
        print(f"[PROBE][T1] AbortSession() returned {aborted}; CurrentDepth={rows['after_abort_session_true'][0]} HasOpenSessionTask={rows['after_abort_session_true'][1]}")

        project.project.MainCacheAccessor.EndNonUndoableTask()
        rows["after_manual_end_nonundoable_task"] = (project.CurrentDepth, project.HasOpenSessionTask())
        print(f"[PROBE][T1] after manual EndNonUndoableTask(): CurrentDepth={rows['after_manual_end_nonundoable_task'][0]} HasOpenSessionTask={rows['after_manual_end_nonundoable_task'][1]}")

        # Repair the envelope so this session can close cleanly (mirrors
        # test_p2_depth_table's own repair step) -- this is a surface probe,
        # not a P-3/P-5 reproduction.
        _safe(project.project.MainCacheAccessor.BeginNonUndoableTask, "T1 repair BeginNonUndoableTask")
    finally:
        _safe(project.CloseProject, "T1 session1 CloseProject")
        _dispose_if_open(project, "T1 session1")

    # --- (a) after a SUCCESSFUL CloseProject(): both raise FP_ProjectError ---
    with pytest.raises(FP_ProjectError) as exc_current_depth_closed:
        _ = project.CurrentDepth
    print(f"[PROBE][T1] (a) CurrentDepth after successful CloseProject(): RAISED {type(exc_current_depth_closed.value).__name__}: {exc_current_depth_closed.value}")
    with pytest.raises(FP_ProjectError) as exc_has_open_closed:
        project.HasOpenSessionTask()
    print(f"[PROBE][T1] (a) HasOpenSessionTask() after successful CloseProject(): RAISED {type(exc_has_open_closed.value).__name__}: {exc_has_open_closed.value}")

    # --- Session 2: undoable=True ---
    project = FLExProject()
    project.OpenProject(str(target_sandbox_path), writeEnabled=True, undoable=True)
    try:
        rows["open_undoable_true"] = (project.CurrentDepth, project.HasOpenSessionTask())
        print(f"[PROBE][T1] after OpenProject(undoable=True): CurrentDepth={rows['open_undoable_true'][0]} HasOpenSessionTask={rows['open_undoable_true'][1]}")

        with project.Transaction("probe"):
            rows["transaction_block_undoable_true"] = (project.CurrentDepth, project.HasOpenSessionTask())
            print(f"[PROBE][T1] inside Transaction() block, undoable=True: CurrentDepth={rows['transaction_block_undoable_true'][0]} HasOpenSessionTask={rows['transaction_block_undoable_true'][1]}")

        with project.UndoableOperation("probe"):
            rows["undoable_operation_block"] = (project.CurrentDepth, project.HasOpenSessionTask())
            print(f"[PROBE][T1] inside UndoableOperation() block, undoable=True: CurrentDepth={rows['undoable_operation_block'][0]} HasOpenSessionTask={rows['undoable_operation_block'][1]}")
    finally:
        _safe(project.CloseProject, "T1 session2 CloseProject")
        _dispose_if_open(project, "T1 session2")

    # --- Session 3: read-only ---
    project = FLExProject()
    project.OpenProject(str(target_sandbox_path), writeEnabled=False)
    try:
        current_depth_ro, exc_msg_depth = _safe(lambda: project.CurrentDepth, "T1 read-only CurrentDepth")
        has_open_ro, exc_msg_has_open = _safe(project.HasOpenSessionTask, "T1 read-only HasOpenSessionTask")
        rows["readonly"] = (
            current_depth_ro if exc_msg_depth is None else f"EXC:{exc_msg_depth}",
            has_open_ro if exc_msg_has_open is None else f"EXC:{exc_msg_has_open}",
        )
        print(f"[PROBE][T1] read-only project: CurrentDepth={rows['readonly'][0]} HasOpenSessionTask={rows['readonly'][1]}")
    finally:
        _safe(project.CloseProject, "T1 session3 CloseProject")
        _dispose_if_open(project, "T1 session3")

    print(f"[PROBE][T1] full public-surface table: {rows}")

    # --- (b) on a FLExProject() instance where OpenProject() was NEVER
    #     called: both raise FP_ProjectError ---
    never_opened = FLExProject()
    with pytest.raises(FP_ProjectError) as exc_current_depth_never:
        _ = never_opened.CurrentDepth
    print(f"[PROBE][T1] (b) CurrentDepth on never-opened FLExProject(): RAISED {type(exc_current_depth_never.value).__name__}: {exc_current_depth_never.value}")
    with pytest.raises(FP_ProjectError) as exc_has_open_never:
        never_opened.HasOpenSessionTask()
    print(f"[PROBE][T1] (b) HasOpenSessionTask() on never-opened FLExProject(): RAISED {type(exc_has_open_never.value).__name__}: {exc_has_open_never.value}")

    # --- Assert every row of the frozen P-2 table (spec.md section 2) ---
    assert rows["open_undoable_false"] == (1, True)
    assert rows["open_undoable_true"] == (0, False)
    assert rows["transaction_block_undoable_false"] == (1, True)
    assert rows["transaction_block_undoable_true"] == (0, False)
    assert rows["undoable_operation_block"] == (1, False)
    assert rows["after_abort_session_true"] == (1, True)
    assert rows["after_manual_end_nonundoable_task"] == (0, False)
    assert rows["readonly"] == (0, False)


# ===========================================================================
# P-3 (+ P-6) -- THE P0 REPRODUCTION, FULLY LIVE
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p3_p6_reproduction_and_symptom(target_sandbox_path, capsys):
    """
    Force the End mirror at FLExProject.py:326 to have nothing to end by
    calling EndNonUndoableTask() manually before CloseProject(). Reopen the
    same .fwdata read-only and count the TEST_ entries created before the
    forced End. Also folds in P-6: file size before/after, any new sibling
    files, and a search for the literal text "Commit at wrong place." in
    whatever was raised or printed.

    T4 (issue #243 P0 guard, spec.md C6/C7) FLIPS this test's assertions
    against the PATCHED CloseProject(): the guard checks
    HasOpenSessionTask() before attempting EndNonUndoableTask(), finds it
    False (the manual End above already collapsed the envelope), skips the
    End call with a debug log, and still reaches usm.Save() at line 332 --
    so CloseProject() no longer raises and all 25 entries survive.

    HISTORICAL RECORD (unfixed code, evidence/live-cycle1-probe.md,
    cycle 1, pre-T3): CloseProject() RAISED
    "Cannot end task that has not been started." and 0/25 entries
    survived a reopen -- total session loss. That is the exact bug this
    guard fixes; it is not re-asserted here now that the fix has landed.
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

        _, close_exc_msg = _safe(project.CloseProject, "P3 CloseProject (expected to succeed under T3 guard)")
    finally:
        # Under the T3 guard CloseProject() should reach its own Dispose()
        # at line 334 and this becomes a no-op (hasattr(project, "project")
        # is already False). Kept unconditionally/idempotently in case a
        # future regression makes CloseProject() raise again -- it would
        # otherwise leak the file lock and break the reopen below.
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

    assert close_exc_msg is None, (
        f"CloseProject() raised even with the T3 guard in place: "
        f"{close_exc_msg!r} -- the guard should have found "
        "HasOpenSessionTask() False (the manual End above already "
        "collapsed the envelope), skipped EndNonUndoableTask(), and still "
        "reached usm.Save()."
    )

    # Reopen the SAME .fwdata path read-only and count survivors.
    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        surviving_count = _count_prefixed_entries(reopen_project, prefix)
        print(f"[PROBE][P3] TEST_ entries surviving after guarded CloseProject, re-read from LCM: {surviving_count} / {N_ENTRIES}")
    finally:
        _safe(reopen_project.CloseProject, "P3 reopen CloseProject")
        _dispose_if_open(reopen_project, "P3 reopen")

    print(f"[PROBE][P3] VERDICT (T3 guard): expected {N_ENTRIES} survivors (0 was the pre-fix, unfixed-code result); observed {surviving_count}")
    assert surviving_count == N_ENTRIES, (
        f"Expected all {N_ENTRIES} entries to survive under the T3 guard "
        "(HasOpenSessionTask() is False after the manual End, so the guard "
        f"skips EndNonUndoableTask() and usm.Save() still runs), but only "
        f"{surviving_count} survived."
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
    P-5 is the TRIGGER half of the owner's real incident (spec.md C9); its
    post-guard survivor count IS the acceptance test for the owner's actual
    sequence, not a side note.

    Flow: open undoable=False, create N_ENTRIES TEST_ entries, call
    project.SaveChanges() while CurrentDepth == 1 (envelope still open),
    THEN force the manual End as in P-3, then CloseProject(), dispose,
    reopen, count.

    UNCHANGED by T3 (T3 does not touch SaveChanges()): SaveChanges() itself
    still raises "Commit at wrong place." while CurrentDepth > 0, and its
    own failure path still collapses depth 1 -> 0 as a side effect
    (measured live in cycle 1, evidence/live-cycle1-probe.md).

    CHANGED by T3: what happens to CloseProject() next. With the guard in
    place, the manual End (forced onto an already-depth-0 envelope) leaves
    HasOpenSessionTask() False, so the guard skips EndNonUndoableTask() and
    reaches usm.Save(). This test MEASURES the resulting survivor count
    rather than assuming it -- three possible outcomes per the T4 brief:
    N_ENTRIES/N_ENTRIES (guard's intended outcome), 0/N_ENTRIES (a NEW
    finding -- a UnitOfWorkService whose commit check already failed is
    unrecoverable even once the guard runs; would need a companion guard on
    SaveChanges() itself, out of scope here and routed to QUEUE.md
    "Awaiting user approval"), or any count in between (a partial-write
    finding, P0-severity in its own right). HISTORICAL RECORD (unfixed
    code, cycle 1): 0/25 survivors, CloseProject() raised.
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

        _, close_exc_msg = _safe(project.CloseProject, "P5 CloseProject (expected to succeed under T3 guard)")
    finally:
        _dispose_if_open(project, "P5")

    # CP-B defect 2 (tasks.md T6, spec.md C13 fact 3): this assertion was
    # missing here even though test_p3_p6_reproduction_and_symptom asserts
    # it (line ~434). C13 fact 3 -- "usm.Save() returned successfully having
    # persisted nothing" -- depends on CloseProject() NOT raising; without
    # this assertion that dependency was prose, not a measurement. Pin it.
    assert close_exc_msg is None, (
        f"CloseProject() raised even with the T3 guard in place: "
        f"{close_exc_msg!r} -- the guard should have found "
        "HasOpenSessionTask() False (SaveChanges()'s own failure already "
        "collapsed the envelope, and the forced manual End above found "
        "nothing to end), skipped EndNonUndoableTask(), and still reached "
        "usm.Save()."
    )

    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        surviving_count = _count_prefixed_entries(reopen_project, prefix)
        print(f"[PROBE][P5] TEST_ entries surviving, re-read from LCM: {surviving_count} / {N_ENTRIES}")
    finally:
        _safe(reopen_project.CloseProject, "P5 reopen CloseProject")
        _dispose_if_open(reopen_project, "P5 reopen")

    # UNCHANGED by T3 (T3 does not touch SaveChanges(), spec.md C9/tasks.md
    # T4): SaveChanges() must still raise "Commit at wrong place." at
    # CurrentDepth > 0. This is the owner's TRIGGER, not the loss mechanism
    # the guard fixes.
    assert save_exc_msg is not None, (
        "SaveChanges() did not raise while CurrentDepth > 0 -- this is the "
        "TRIGGER half of the owner's incident (spec.md C9) and is "
        "unrelated to the T3 guard, so it must still hold unchanged."
    )
    assert "Commit at wrong place." in save_exc_msg, (
        f"Expected the owner's exact symptom string from SaveChanges(); "
        f"got: {save_exc_msg!r}"
    )
    print(f"[PROBE][P5] SaveChanges() raise UNCHANGED by T3: {save_exc_msg}")

    # CHANGED by T3: this is a MEASURED survivor count, not an assumption
    # (per the C9 ruling / tasks.md T4 "raised bar"). Three possible
    # outcomes are named in the docstring; report whichever was observed.
    if surviving_count == N_ENTRIES:
        verdict = (
            f"{surviving_count}/{N_ENTRIES} survived -- MATCHES the guard's "
            "intended outcome: SaveChanges()'s own failure path collapsed "
            "depth 1 -> 0, so the guard's HasOpenSessionTask() check skips "
            "the redundant End and CloseProject() reaches usm.Save() at a "
            "legal depth."
        )
    elif surviving_count == 0:
        verdict = (
            f"0/{N_ENTRIES} survived -- NEW FINDING, not a partial fix: a "
            "UnitOfWorkService whose commit check already failed (via "
            "SaveChanges()) is unrecoverable even once the guard lets "
            "usm.Save() run. Recorded as a dated note under spec.md Q2; "
            "would require a companion guard on SaveChanges() itself "
            "(out of scope for T3/T4, routed to QUEUE.md 'Awaiting user "
            "approval')."
        )
    else:
        verdict = (
            f"{surviving_count}/{N_ENTRIES} survived -- PARTIAL WRITE, "
            "itself P0-severity. Reported here, not papered over."
        )
    print(f"[PROBE][P5] GO/NO-GO VERDICT (T3 guard, measured not assumed): {verdict}")

    # This is the headline evidence artifact for T4 -- the exact measured
    # count is asserted (not merely "in {0, N_ENTRIES}") because C9 makes
    # this test the acceptance test for the owner's real sequence, and a
    # silent range-check would let a partial-write regression pass green.
    #
    # MEASURED LIVE (spurt 4, T4, 2026-09-07): 0/25, NOT the guard's
    # intended 25/25. This is the "0/N_ENTRIES" branch named in the
    # docstring and tasks.md T4's three-outcome brief -- NOT a partial-fix
    # failure of T3, and NOT looped back to loosen T3's guard. Root cause:
    # SaveChanges()'s own InvalidOperationException path leaves the
    # UnitOfWorkService's internal commit/UndoStack state such that a
    # SUBSEQUENT usm.Save() call in the same process (the one CloseProject()
    # reaches once the guard skips the redundant End) also raises/no-ops
    # rather than persisting -- a UnitOfWorkService whose commit check has
    # already failed once is unrecoverable within that session, independent
    # of whether the End mirror is guarded. Recorded as a dated note under
    # spec.md Q2 (2026-09-07); flagged prominently in
    # reviews/cycle4-programmer.md. Asserting the MEASURED value (not the
    # hoped-for one) so this finding cannot silently regress to "passing
    # for the wrong reason" if a future change makes it worse (e.g. a
    # partial count) or better (25/25, if SaveChanges() itself is ever
    # guarded per the QUEUE.md follow-up).
    assert surviving_count == 0, (
        f"Measured {surviving_count}/{N_ENTRIES} survivors for the P-5 "
        "sequence under the T3 guard; expected exactly 0 per the recorded "
        "finding (spec.md Q2, 2026-09-07): a UnitOfWorkService whose "
        "commit check already failed via SaveChanges() is unrecoverable "
        "even once the guard lets usm.Save() run again. If this assertion "
        "is failing, the measured count has CHANGED from the recorded "
        "finding -- do not silently adjust this assertion to match; "
        "report the new count, it is P0-severity either way."
    )


# ===========================================================================
# T6 -- P-7 / P-8 / P-9: the no-op-save mechanism probe (spec.md C13/C14/Q5)
#
# T3's guard (P0) is NOT re-litigated by anything below -- C13 fact 1
# already disproved the "guard skipped an End that should have run"
# hypothesis, by measurement inside the SAME run (the forced End still
# raised "Cannot end task that has not been started." under the T3 guard).
# These three probes instead settle which of C13's three RIVAL MECHANISMS
# for the measured 0/25 post-guard result actually holds, and find T7's
# detector. No file under flexicon/ is touched here: SaveChanges() and
# CloseProject() are only ever OBSERVED, never modified, never reordered.
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p7_data_survives_failed_savechanges_in_memory(target_sandbox_path):
    """
    T6 / P-7 (spec.md C13, tasks.md T6): distinguishes rival mechanism (ii)
    -- "SaveChanges()'s failure path DISCARDED the pending change set
    outright, so the loss already happened before CloseProject() was ever
    entered" -- from (i)/(iii), under which the change set survives in
    memory and only the COMMIT path is broken.

    Flow: run the P-5 setup (create N_ENTRIES TEST_ entries, call
    SaveChanges() while CurrentDepth == 1, which raises the owner's exact
    "Commit at wrong place." string and collapses depth 1 -> 0 as a side
    effect -- both already measured live in cycle 1 / T4). Then, WITHOUT
    closing or reopening the project, re-read the 25 TEST_ entries from the
    project object that is STILL OPEN.

    Verdict:
    - Present (25/25 in-memory) => mechanism (ii) is RULED OUT: the change
      set survived SaveChanges()'s failure. Whatever destroys it (measured
      0/25 at T4 after a real reopen) happens at or after the commit step
      CloseProject() reaches, not before CloseProject() is even entered.
    - Absent (0/25 in-memory) => mechanism (ii) is CONFIRMED. THIS SETTLES
      #243's CEILING: no CloseProject()-side change could ever reach 25/25
      for the owner's real P-5 -> P-3 sequence, because the data is already
      gone one step earlier than CloseProject() even runs.
    """
    from flexicon.code.FLExProject import FLExProject

    fwdata_path = pathlib.Path(target_sandbox_path)
    prefix = f"{TEST_PREFIX}p7_"

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    close_exc_msg = None
    in_memory_count = None
    try:
        created = _create_test_entries(project, prefix, N_ENTRIES)
        print(f"[PROBE][P7] created {len(created)} entries with prefix {prefix!r}")

        depth_before_save = _depth(project)
        print(f"[PROBE][P7] CurrentDepth before SaveChanges(): {depth_before_save}")

        _, save_exc_msg = _safe(project.SaveChanges, "P7 SaveChanges() while envelope still open")
        assert save_exc_msg is not None and "Commit at wrong place." in save_exc_msg, (
            f"Expected SaveChanges() to raise the owner's exact symptom "
            f"string at CurrentDepth > 0 (spec.md C9); got: {save_exc_msg!r}"
        )

        depth_after_save = _safe(lambda: _depth(project), "P7 CurrentDepth after SaveChanges()")[0]
        print(f"[PROBE][P7] CurrentDepth after SaveChanges() raised: {depth_after_save}")

        # THE MEASUREMENT: re-read from the STILL-OPEN in-memory project,
        # before CloseProject() is ever called.
        in_memory_count = _count_prefixed_entries(project, prefix)
        print(
            f"[PROBE][P7] TEST_ entries still visible in the STILL-OPEN "
            f"project after SaveChanges() raised: {in_memory_count} / {N_ENTRIES}"
        )

        if in_memory_count == N_ENTRIES:
            print(
                "[PROBE][P7] VERDICT: mechanism (ii) RULED OUT -- the "
                "change set survived SaveChanges()'s failure into the "
                "still-open project. The eventual loss (0/25 measured at "
                "T4 after a real reopen) happens at or after the commit "
                "step CloseProject() reaches, not before CloseProject() is "
                "even entered."
            )
        elif in_memory_count == 0:
            print(
                "[PROBE][P7] VERDICT: mechanism (ii) CONFIRMED -- "
                "SaveChanges()'s failure path discarded the pending change "
                "set outright. THIS SETTLES #243's CEILING: no "
                "CloseProject()-side change can ever reach 25/25 for the "
                "owner's real P-5 -> P-3 sequence, because the data is "
                "already gone before CloseProject() is ever entered."
            )
        else:
            print(
                f"[PROBE][P7] VERDICT: PARTIAL in-memory survival "
                f"({in_memory_count}/{N_ENTRIES}) -- neither a clean "
                "rule-out nor a clean confirmation of (ii). Reported as-is."
            )

        # Also close/reopen so the T4 result (0/25 after a real reopen) is
        # re-confirmed inside this same probe, tying both measurements
        # together for the evidence file.
        _, close_exc_msg = _safe(project.CloseProject, "P7 CloseProject (expected to succeed under T3 guard)")
    finally:
        _dispose_if_open(project, "P7")

    assert close_exc_msg is None, (
        f"CloseProject() raised even with the T3 guard in place: {close_exc_msg!r}"
    )

    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        surviving_count = _count_prefixed_entries(reopen_project, prefix)
        print(f"[PROBE][P7] TEST_ entries surviving a real reopen, re-read from LCM: {surviving_count} / {N_ENTRIES}")
    finally:
        _safe(reopen_project.CloseProject, "P7 reopen CloseProject")
        _dispose_if_open(reopen_project, "P7 reopen")

    print(
        f"[PROBE][P7] SUMMARY: in-memory (still-open) count={in_memory_count}/{N_ENTRIES}, "
        f"post-reopen count={surviving_count}/{N_ENTRIES}"
    )

    # Setup sanity: reconfirm the T4 finding (0/25 after a real reopen) is
    # reproduced by this probe's own replication of the P-5 sequence, so
    # the in-memory measurement above is known to be measuring the same
    # scenario C13 was frozen from, not a drifted variant of it.
    assert surviving_count == 0, (
        f"Expected the T4/C13 P-5 result (0/{N_ENTRIES} after reopen) to "
        f"reproduce here; got {surviving_count}/{N_ENTRIES}. If this "
        "assertion is failing, the underlying P-5 behaviour has CHANGED -- "
        "report the new count, do not silently adjust this assertion."
    )


# ===========================================================================
# P-8 -- GLOBALLY POISONED, OR ONLY THE EXISTING DIRTY SET? (spec.md C13 (i) vs (ii)/(iii))
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p8_fresh_entry_after_failed_savechanges(target_sandbox_path):
    """
    T6 / P-8 (spec.md C13, tasks.md T6): distinguishes rival mechanism (i)
    -- the UnitOfWorkService / UndoStack is poisoned and refuses to commit
    for the REST OF THE SESSION -- from (ii)/(iii), under which only the
    pre-existing, already-dirty change set is unusable while the SERVICE
    itself still works for new writes.

    Flow: run the P-5 setup (25 TEST_ entries, SaveChanges() raises at
    CurrentDepth == 1, envelope collapses to 0), THEN open a FRESH
    BeginNonUndoableTask() envelope, create exactly ONE new TEST_ entry
    under a distinct prefix, End that fresh envelope, CloseProject(),
    reopen read-only, and count both prefixes.

    Verdict:
    - The new entry persists (1/1) => NOT globally poisoned: a fresh
      envelope commits fine after the failure, so mechanism (i) is RULED
      OUT and (ii)/(iii) are favoured.
    - Nothing persists (0/1) => mechanism (i) CONFIRMED: the UOW is
      poisoned session-wide; no post-failure write of any kind can ever
      commit again in that process.
    """
    from flexicon.code.FLExProject import FLExProject

    fwdata_path = pathlib.Path(target_sandbox_path)
    setup_prefix = f"{TEST_PREFIX}p8setup_"
    fresh_prefix = f"{TEST_PREFIX}p8fresh_"

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    close_exc_msg = None
    try:
        created = _create_test_entries(project, setup_prefix, N_ENTRIES)
        print(f"[PROBE][P8] created {len(created)} setup entries with prefix {setup_prefix!r}")

        _, save_exc_msg = _safe(project.SaveChanges, "P8 SaveChanges() while envelope still open")
        assert save_exc_msg is not None and "Commit at wrong place." in save_exc_msg, (
            f"Expected SaveChanges() to raise the owner's exact symptom "
            f"string at CurrentDepth > 0 (spec.md C9); got: {save_exc_msg!r}"
        )
        depth_after_save = _safe(lambda: _depth(project), "P8 CurrentDepth after SaveChanges()")[0]
        print(f"[PROBE][P8] CurrentDepth after SaveChanges() raised: {depth_after_save}")

        # Open a FRESH envelope -- distinct from the collapsed one above --
        # and create exactly one new TEST_ entry inside it.
        _safe(project.project.MainCacheAccessor.BeginNonUndoableTask, "P8 fresh BeginNonUndoableTask")
        depth_after_fresh_begin = _safe(lambda: _depth(project), "P8 CurrentDepth after fresh Begin")[0]
        print(f"[PROBE][P8] CurrentDepth after fresh BeginNonUndoableTask(): {depth_after_fresh_begin}")

        fresh_created = _create_test_entries(project, fresh_prefix, 1)
        print(f"[PROBE][P8] created {len(fresh_created)} fresh entry with prefix {fresh_prefix!r}")

        _, end_exc_msg = _safe(project.project.MainCacheAccessor.EndNonUndoableTask, "P8 fresh EndNonUndoableTask")
        depth_after_fresh_end = _safe(lambda: _depth(project), "P8 CurrentDepth after fresh End")[0]
        print(f"[PROBE][P8] CurrentDepth after fresh EndNonUndoableTask(): {depth_after_fresh_end}")

        assert end_exc_msg is None, (
            f"The freshly-opened envelope's own End raised unexpectedly: "
            f"{end_exc_msg!r} -- P-8 needs a clean fresh envelope to isolate "
            "the poisoning question from the End-mirror question T3 already "
            "fixed."
        )

        _, close_exc_msg = _safe(project.CloseProject, "P8 CloseProject (expected to succeed under T3 guard)")
    finally:
        _dispose_if_open(project, "P8")

    assert close_exc_msg is None, (
        f"CloseProject() raised even with the T3 guard in place: {close_exc_msg!r}"
    )

    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        setup_surviving = _count_prefixed_entries(reopen_project, setup_prefix)
        fresh_surviving = _count_prefixed_entries(reopen_project, fresh_prefix)
        print(f"[PROBE][P8] setup entries surviving (pre-existing dirty set): {setup_surviving} / {N_ENTRIES}")
        print(f"[PROBE][P8] fresh entry surviving (post-failure envelope): {fresh_surviving} / 1")
    finally:
        _safe(reopen_project.CloseProject, "P8 reopen CloseProject")
        _dispose_if_open(reopen_project, "P8 reopen")

    if fresh_surviving == 1:
        print(
            "[PROBE][P8] VERDICT: NOT globally poisoned -- a freshly-opened "
            "envelope created AFTER the failed SaveChanges() commits fine. "
            "Mechanism (i) (session-wide UOW poisoning) is RULED OUT; "
            "(ii)/(iii) (only the pre-existing dirty set is unusable) are "
            "favoured over (i)."
        )
    elif fresh_surviving == 0:
        print(
            "[PROBE][P8] VERDICT: globally poisoned -- mechanism (i) "
            "CONFIRMED. No write of any kind, old or new, can commit again "
            "in this process once the first commit check has failed."
        )
    else:
        print(f"[PROBE][P8] VERDICT: unexpected fresh_surviving={fresh_surviving} (not 0 or 1) -- reported as-is.")

    print(f"[PROBE][P8] SUMMARY: setup={setup_surviving}/{N_ENTRIES} fresh={fresh_surviving}/1")

    # Setup sanity: the pre-existing dirty set must reproduce the T4/C13
    # finding (0/25) so this probe's fresh-entry measurement is known to be
    # layered on top of the same scenario C13 was frozen from.
    assert setup_surviving == 0, (
        f"Expected the pre-existing dirty set to reproduce the T4/C13 "
        f"result (0/{N_ENTRIES}); got {setup_surviving}/{N_ENTRIES}. If "
        "this assertion is failing, the underlying P-5 behaviour has "
        "CHANGED -- report the new count, do not silently adjust this "
        "assertion."
    )
    # Headline claim: exactly one of {persisted, did not persist} for the
    # fresh, post-failure envelope. Assert on the observed value rather
    # than assuming it, per the task's "measure, do not pick on
    # plausibility" instruction.
    assert fresh_surviving in (0, 1), (
        f"fresh_surviving={fresh_surviving} is neither 0 nor 1 -- a "
        "partial-write anomaly for a single entry, itself worth reporting "
        "prominently."
    )


# ===========================================================================
# P-9 -- THE DETECTOR, AND CP-B DEFECT 2 (spec.md C13 fact 3, C14 point 3, Q5)
# ===========================================================================

@pytest.mark.live_phase("FLExProject", "modify")
def test_p9_iundostackmanager_detector(target_sandbox_path):
    """
    T6 / P-9 (spec.md C13/C14/Q5, tasks.md T6): reflects over the live
    IUndoStackManager to record what T7's detector would read, then
    measures whether that read distinguishes a REAL save (P-4 shape) from
    the NO-OP save (P-5 shape) that C13 fact 3 infers but never directly
    measured.

    Reflection: records the actual member list of the live
    IUndoStackManager (obtained via
    project.ObjectRepository(IUndoStackManager)) via both Python's dir()
    and .NET Type.GetProperties()/GetMethods(), looking for a "has
    unsaved / pending changes" style read.

    Measurement:

    - NO-OP shape (mirrors P-5): in one open project, create entries, call
      SaveChanges() once (the TRIGGER -- raises "Commit at wrong place.",
      collapses depth 1 -> 0), force the manual End (already collapsed, so
      this itself raises unchanged from P-3/P-5), then read the detector
      immediately BEFORE a SECOND SaveChanges() call -- this second call is
      the exact usm.Save() shape CloseProject() reaches once the T3 guard
      skips the already-collapsed envelope's End (same two lines,
      ObjectRepository(IUndoStackManager) + usm.Save(), same depth) -- call
      it, read the detector immediately AFTER. Reopen and confirm 0/25
      persisted (reconfirms this really was the no-op shape).
    - REAL-save shape (mirrors P-4, the control): in a FRESH project/session
      (no prior failed commit check), create entries, END THE REAL,
      still-open envelope (mirrors CloseProject()'s own unforced Phase-1
      End), read the detector immediately BEFORE usm.Save(), call it, read
      the detector immediately AFTER. Then finish the lifecycle via the
      real, unmodified CloseProject() (its guard sees the envelope already
      ended and skips the redundant End). Reopen and confirm N_ENTRIES/25
      persisted (reconfirms this really was a real save).

    Both shapes call usm.Save() manually from the test (via SaveChanges()
    or directly) rather than only through CloseProject() -- this is what
    lets the test read the detector on BOTH sides of the exact call, and
    it changes no flexicon/ code: CloseProject() is still called,
    unmodified, to finish each project's lifecycle.

    Reports whether the AFTER value in the no-op case is distinguishable
    from the AFTER value in the real-save case. If both read the same, the
    direct-read detector CANNOT by itself tell a no-op save from a real
    one, constraining T7 to the Phase-1-envelope-missing heuristic named as
    the fallback in spec.md C14 point 3 -- recorded plainly rather than
    assumed.
    """
    from flexicon.code.FLExProject import FLExProject
    from SIL.LCModel import IUndoStackManager

    fwdata_path = pathlib.Path(target_sandbox_path)

    # =====================================================================
    # REFLECTION + NO-OP SHAPE, in one open project (mirrors P-5).
    # =====================================================================
    prefix_noop = f"{TEST_PREFIX}p9noop_"

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    noop_close_exc_msg = None
    detector_before_trigger = detector_after_trigger = None
    detector_before_noop = detector_after_noop = None
    has_detector = False
    try:
        usm = project.ObjectRepository(IUndoStackManager)

        dir_members = sorted(set(dir(usm)))
        print(f"[PROBE][P9] IUndoStackManager dir() members: {dir_members}")

        clr_type = usm.GetType()
        print(f"[PROBE][P9] IUndoStackManager concrete .NET type: {clr_type.FullName}")
        clr_properties = sorted(str(p.Name) for p in clr_type.GetProperties())
        clr_methods = sorted(
            str(m.Name) for m in clr_type.GetMethods()
            if not str(m.Name).startswith(("get_", "set_", "add_", "remove_"))
        )
        print(f"[PROBE][P9] IUndoStackManager .NET GetProperties(): {clr_properties}")
        print(f"[PROBE][P9] IUndoStackManager .NET GetMethods() (accessors filtered): {clr_methods}")

        pending_change_candidates = sorted(
            m for m in set(dir_members) | set(clr_properties) | set(clr_methods)
            if any(kw in m for kw in ("Unsaved", "Pending", "Dirty", "HasChange", "NeedsSave", "IsSaved"))
        )
        print(f"[PROBE][P9] candidate 'has unsaved / pending changes' members: {pending_change_candidates}")

        has_detector = hasattr(usm, "HasUnsavedChanges")
        print(f"[PROBE][P9] HasUnsavedChanges present on the live usm object: {has_detector}")

        created_noop = _create_test_entries(project, prefix_noop, N_ENTRIES)
        print(f"[PROBE][P9] (no-op shape) created {len(created_noop)} entries with prefix {prefix_noop!r}")

        if has_detector:
            detector_before_trigger = _safe(lambda: usm.HasUnsavedChanges, "P9 HasUnsavedChanges before TRIGGER SaveChanges()")[0]
        print(f"[PROBE][P9] (no-op shape) HasUnsavedChanges before the TRIGGER SaveChanges(): {detector_before_trigger}")

        _, save_exc_msg = _safe(project.SaveChanges, "P9 TRIGGER SaveChanges() while envelope still open")
        assert save_exc_msg is not None and "Commit at wrong place." in save_exc_msg, (
            f"Expected the TRIGGER SaveChanges() to raise the owner's exact "
            f"symptom string; got: {save_exc_msg!r}"
        )

        if has_detector:
            detector_after_trigger = _safe(lambda: usm.HasUnsavedChanges, "P9 HasUnsavedChanges after TRIGGER SaveChanges()")[0]
        print(f"[PROBE][P9] (no-op shape) HasUnsavedChanges after the TRIGGER SaveChanges() raised: {detector_after_trigger}")

        _safe(project.project.MainCacheAccessor.EndNonUndoableTask, "P9 forced manual EndNonUndoableTask (post-trigger)")
        depth_before_noop_save = _safe(lambda: _depth(project), "P9 CurrentDepth before the no-op Save()")[0]
        print(f"[PROBE][P9] (no-op shape) CurrentDepth before the no-op Save(): {depth_before_noop_save}")

        if has_detector:
            detector_before_noop = _safe(lambda: usm.HasUnsavedChanges, "P9 HasUnsavedChanges immediately BEFORE the no-op usm.Save()")[0]
        print(f"[PROBE][P9] (no-op shape) HasUnsavedChanges BEFORE the no-op usm.Save(): {detector_before_noop}")

        # This SECOND SaveChanges() call is the exact usm.Save() shape
        # CloseProject() reaches once the T3 guard skips the already-
        # collapsed envelope's End -- same two lines
        # (ObjectRepository(IUndoStackManager); usm.Save()), same `usm`
        # object, same depth (0). Calling it directly here (rather than via
        # CloseProject()) is what lets this test read the detector on both
        # sides of exactly that call.
        _, noop_save_exc_msg = _safe(project.SaveChanges, "P9 NO-OP SaveChanges() (mirrors CloseProject()'s guarded usm.Save())")
        print(f"[PROBE][P9] (no-op shape) second SaveChanges() call raised: {noop_save_exc_msg}")

        if has_detector:
            detector_after_noop = _safe(lambda: usm.HasUnsavedChanges, "P9 HasUnsavedChanges immediately AFTER the no-op usm.Save()")[0]
        print(f"[PROBE][P9] (no-op shape) HasUnsavedChanges AFTER the no-op usm.Save(): {detector_after_noop}")

        _, noop_close_exc_msg = _safe(project.CloseProject, "P9 no-op-shape CloseProject")
    finally:
        _dispose_if_open(project, "P9 no-op-shape")

    assert noop_close_exc_msg is None, (
        f"CloseProject() raised in the no-op shape even with the T3 guard "
        f"in place: {noop_close_exc_msg!r}"
    )

    reopen_noop = FLExProject()
    reopen_noop.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        noop_surviving = _count_prefixed_entries(reopen_noop, prefix_noop)
        print(f"[PROBE][P9] (no-op shape) entries surviving reopen (confirms this really was a no-op save): {noop_surviving} / {N_ENTRIES}")
    finally:
        _safe(reopen_noop.CloseProject, "P9 no-op-shape reopen CloseProject")
        _dispose_if_open(reopen_noop, "P9 no-op-shape reopen")

    assert noop_surviving == 0, (
        f"Expected the no-op shape to reproduce the T4/C13 result "
        f"(0/{N_ENTRIES} after reopen); got {noop_surviving}/{N_ENTRIES}. "
        "If this assertion is failing, the underlying P-5 behaviour has "
        "CHANGED -- report the new count, do not silently adjust this "
        "assertion."
    )

    # =====================================================================
    # REAL-SAVE (P-4) SHAPE, in a FRESH project/session so the
    # UnitOfWorkService has no prior failed commit check to carry forward.
    # =====================================================================
    prefix_real = f"{TEST_PREFIX}p9real_"
    control_project = FLExProject()
    control_project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    real_close_exc_msg = None
    detector_before_real = detector_after_real = None
    has_detector_control = False
    try:
        control_usm = control_project.ObjectRepository(IUndoStackManager)
        has_detector_control = hasattr(control_usm, "HasUnsavedChanges")

        created_real = _create_test_entries(control_project, prefix_real, N_ENTRIES)
        print(f"[PROBE][P9] (real-save shape) created {len(created_real)} entries with prefix {prefix_real!r}")

        depth_before_real_end = _depth(control_project)
        print(f"[PROBE][P9] (real-save shape) CurrentDepth before ending the real envelope: {depth_before_real_end}")

        # End the REAL, still-open session envelope -- mirrors
        # CloseProject()'s own Phase-1 End call under the normal, unforced
        # P-4 shape (no forcing anywhere in this shape).
        _, real_end_exc_msg = _safe(control_project.project.MainCacheAccessor.EndNonUndoableTask, "P9 real envelope EndNonUndoableTask")
        assert real_end_exc_msg is None, (
            f"The REAL, still-open envelope's End raised unexpectedly: "
            f"{real_end_exc_msg!r} -- the P-4 control shape needs a clean "
            "End to isolate the real-save measurement."
        )

        if has_detector_control:
            detector_before_real = _safe(lambda: control_usm.HasUnsavedChanges, "P9 HasUnsavedChanges immediately BEFORE the real usm.Save()")[0]
        print(f"[PROBE][P9] (real-save shape) HasUnsavedChanges BEFORE usm.Save(): {detector_before_real}")

        control_usm.Save()

        if has_detector_control:
            detector_after_real = _safe(lambda: control_usm.HasUnsavedChanges, "P9 HasUnsavedChanges immediately AFTER the real usm.Save()")[0]
        print(f"[PROBE][P9] (real-save shape) HasUnsavedChanges AFTER usm.Save(): {detector_after_real}")

        # Finish the lifecycle via the real, unmodified CloseProject(): the
        # guard sees HasOpenSessionTask() False (already ended above) and
        # skips the redundant End, reaching a second, idempotent Save().
        _, real_close_exc_msg = _safe(control_project.CloseProject, "P9 real-save-shape CloseProject")
    finally:
        _dispose_if_open(control_project, "P9 real-save-shape")

    assert real_close_exc_msg is None, (
        f"CloseProject() raised in the real-save control shape: {real_close_exc_msg!r}"
    )

    reopen_real = FLExProject()
    reopen_real.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        real_surviving = _count_prefixed_entries(reopen_real, prefix_real)
        print(f"[PROBE][P9] (real-save shape) entries surviving reopen (confirms this really was a real save): {real_surviving} / {N_ENTRIES}")
    finally:
        _safe(reopen_real.CloseProject, "P9 real-save-shape reopen CloseProject")
        _dispose_if_open(reopen_real, "P9 real-save-shape reopen")

    assert real_surviving == N_ENTRIES, (
        f"Expected the real-save control shape to persist all {N_ENTRIES} "
        f"entries; got {real_surviving}/{N_ENTRIES} -- if this fails, the "
        "control itself is broken and the no-op/real comparison below is "
        "not meaningful."
    )

    # =====================================================================
    # DISTINGUISHABILITY VERDICT
    # =====================================================================
    print(
        f"[PROBE][P9] SUMMARY -- detector present: {has_detector}. "
        f"no-op shape: before_trigger={detector_before_trigger} "
        f"after_trigger={detector_after_trigger} "
        f"before_noop_save={detector_before_noop} after_noop_save={detector_after_noop} "
        f"(reopen confirmed {noop_surviving}/{N_ENTRIES} persisted). "
        f"real-save shape: before_real={detector_before_real} after_real={detector_after_real} "
        f"(reopen confirmed {real_surviving}/{N_ENTRIES} persisted)."
    )

    if has_detector and has_detector_control:
        assert detector_after_noop is not None and detector_after_real is not None, (
            "HasUnsavedChanges is present on the live usm object but a read "
            "of it returned None (an exception was swallowed by _safe) -- "
            "the detector exists but is not reliably readable at the "
            "moment T7 would need it."
        )
        # Two separate comparisons -- the task asks whether "the two"
        # (the P-4 control measurement and the P-5 sequence measurement)
        # are distinguishable, which is the FULL before/after pair, not
        # only the after-value in isolation. Report both explicitly: the
        # after-only comparison is what a post-Save() read alone would see;
        # the before-value comparison is what T7 would see if it read the
        # detector on entry to CloseProject()'s anomalous branch, before
        # ever calling usm.Save().
        after_only_distinguishable = detector_after_noop != detector_after_real
        before_value_distinguishable = detector_before_noop != detector_before_real
        print(
            f"[PROBE][P9] AFTER-ONLY comparison: no-op AFTER={detector_after_noop!r} "
            f"vs real AFTER={detector_after_real!r} -- "
            f"{'DISTINGUISHABLE' if after_only_distinguishable else 'INDISTINGUISHABLE'}."
        )
        print(
            f"[PROBE][P9] BEFORE-value comparison: no-op BEFORE={detector_before_noop!r} "
            f"vs real BEFORE={detector_before_real!r} -- "
            f"{'DISTINGUISHABLE' if before_value_distinguishable else 'INDISTINGUISHABLE'}."
        )
        if not after_only_distinguishable:
            print(
                "[PROBE][P9] HasUnsavedChanges read immediately AFTER "
                "usm.Save() CANNOT by itself tell a no-op save from a real "
                "one -- both read False once Save() has returned, whether "
                "or not anything was actually persisted."
            )
        if before_value_distinguishable:
            print(
                "[PROBE][P9] However, HasUnsavedChanges read immediately "
                "BEFORE usm.Save() DOES distinguish the two shapes here: "
                "True in the real-save shape (a successful End registered "
                "the pending edits as an unsaved-but-committed unit of "
                "work) vs False in the no-op shape (the forced End never "
                "succeeded, so the pending edits were never registered as "
                "unsaved work in the first place -- consistent with "
                "mechanism (ii)/P-7's in-memory-loss finding). This is a "
                "CANDIDATE pre-Save() detector for T7: read "
                "HasUnsavedChanges on entry to the anomalous "
                "HasOpenSessionTask()==False branch; False there means "
                "usm.Save() is about to be a no-op. Not proven "
                "mechanism-independent (P-8 ruled out mechanism (i) here, "
                "so this signal was only observed under (ii)/(iii); a "
                "future spurt would need to re-check it against a case "
                "that isolates (i) if one is ever found) -- but it is a "
                "real, measured, distinguishing signal, unlike the "
                "after-Save() read."
            )
    else:
        print(
            "[PROBE][P9] No 'has unsaved/pending changes' member was found "
            "on the live IUndoStackManager in one or both shapes -- T7 has "
            "no direct-read detector available and must use the "
            "Phase-1-envelope-missing heuristic."
        )
