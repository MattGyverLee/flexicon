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
