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
#   Uses target_sandbox_path (tests/flex_plugin.py) exclusively for the P-3/
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

@pytest.mark.requires_live_project
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

@pytest.mark.requires_live_project
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

@pytest.mark.requires_live_project
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

@pytest.mark.requires_live_project
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

@pytest.mark.requires_live_project
@pytest.mark.live_phase("FLExProject", "modify")
def test_p4_control_run_normal_close(target_sandbox_path, caplog):
    """
    Identical flow to P-3 but WITHOUT the manual End -- CloseProject() runs
    normally. Proves the P-3 loss is caused by ordering, not by the sandbox.

    T7 (spec.md C18/C23) negative check: this run's envelope is ended by
    CloseProject() itself (HasOpenSessionTask() reads True, the normal
    "if" branch), so the anomaly branch's ERROR log must NOT fire here --
    contrast with P-5 below, where it does.
    """
    import logging as _logging

    from flexicon.code.FLExProject import FLExProject

    fwdata_path = pathlib.Path(target_sandbox_path)
    prefix = f"{TEST_PREFIX}p4_"

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    close_exc_msg = None
    with caplog.at_level(_logging.ERROR, logger="flexicon.code.FLExProject"):
        try:
            created = _create_test_entries(project, prefix, N_ENTRIES)
            print(f"[PROBE][P4] created {len(created)} entries with prefix {prefix!r}")

            _, close_exc_msg = _safe(project.CloseProject, "P4 CloseProject (expected to succeed)")
        finally:
            _dispose_if_open(project, "P4")

    assert close_exc_msg is None, f"CloseProject() raised unexpectedly in the control run: {close_exc_msg}"

    anomaly_records = [r for r in caplog.records if "HasOpenSessionTask() read False" in r.message]
    print(f"[PROBE][P4] anomaly ERROR records logged (expected 0): {len(anomaly_records)}")
    assert not anomaly_records, (
        "T7's anomaly ERROR must NOT fire on a normal close where "
        f"CloseProject() itself ends the still-open envelope; found: "
        f"{[r.message for r in anomaly_records]}"
    )

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

@pytest.mark.requires_live_project
@pytest.mark.live_phase("FLExProject", "modify")
def test_p5_save_before_forced_end(target_sandbox_path, caplog):
    """
    P-5 is the TRIGGER half of the owner's real incident (spec.md C9); its
    post-guard survivor count IS the acceptance test for the owner's actual
    sequence, not a side note.

    T7 addition (spec.md C18/C23): after the manual End above, this run's
    envelope is already closed by the time CloseProject() is entered, so
    CloseProject() takes the anomaly ("else:") branch and must log the
    ERROR record naming it -- this is the one live route T8b leaves into
    that branch (a stray/forced End with the change set intact, save
    SUCCEEDS). The assertion below pins that the record fires, at ERROR
    level, and asserts nothing about data loss in its message.

    Flow: open undoable=False, create N_ENTRIES TEST_ entries, call
    project.SaveChanges() while CurrentDepth == 1 (envelope still open),
    THEN call the manual End as in P-3, then CloseProject(), dispose,
    reopen, count.

    CHANGED by T8b (the SaveChanges() depth guard, spec.md C20/C21): this
    inverts the T3-era contract pinned above the fold. SaveChanges() now
    reads CurrentDepth and refuses with FP_TransactionError BEFORE
    usm.Save() is ever attempted -- so the owner's exact "Commit at wrong
    place." string no longer reaches the caller here, and (unlike the
    pre-guard liblcm mechanism, which collapsed the envelope 1 -> 0 as a
    side effect of the failed commit check) CurrentDepth is left UNCHANGED
    by the refused call, because the guard never touches LCM state -- it
    only reads it. The manual "End" call below is therefore no longer
    forcing a double-end onto an already-collapsed envelope (as it was
    pre-guard, and still is in P-3's true double-End scenario): the
    envelope is genuinely still open, so this End call is now a normal,
    successful End of the real session envelope -- functionally identical
    to what CloseProject() would have done itself. The pending change set
    was never touched by any failed commit attempt, so it commits
    normally. CloseProject() then finds HasOpenSessionTask() False
    (already ended above), skips its own End, and reaches usm.Save() at a
    legal depth (0) with an intact, untouched change set.

    PREDICTED (not yet measured at authoring time): N_ENTRIES/N_ENTRIES
    survive. This is a genuine PREDICTION derived from the guard's design,
    not a value carried over from the pre-guard T4 measurement (which was
    0/25, under the OLD unguarded mechanism -- see the historical record
    below). If the live measurement differs, that is a P0 finding to
    report verbatim, not an assertion to quietly retune.

    HISTORICAL RECORD (pre-T8b, i.e. the T3-only guard with no
    SaveChanges() guard, spurt 4, 2026-09-07): SaveChanges() raised the raw
    "Commit at wrong place." and collapsed depth 1 -> 0 as a side effect;
    the forced manual End then found nothing to end (envelope already
    collapsed) and raised "Cannot end task that has not been started.";
    CloseProject()'s T3 guard saw HasOpenSessionTask() False, skipped its
    own End, and reached usm.Save() -- which returned successfully having
    persisted NOTHING (0/25 survivors, per C13/C16). That entire chain
    depended on SaveChanges() actually calling usm.Save() and failing; T8b
    removes that call from the chain entirely.
    """
    import logging as _logging

    from flexicon.code.FLExProject import FLExProject
    from flexicon.code.exceptions import FP_TransactionError  # noqa: F401 (documents the expected type)

    fwdata_path = pathlib.Path(target_sandbox_path)
    prefix = f"{TEST_PREFIX}p5_"

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    save_exc_msg = None
    end_exc_msg = None
    close_exc_msg = None
    with caplog.at_level(_logging.ERROR, logger="flexicon.code.FLExProject"):
        try:
            created = _create_test_entries(project, prefix, N_ENTRIES)
            print(f"[PROBE][P5] created {len(created)} entries with prefix {prefix!r}")

            depth_before_save = _depth(project)
            print(f"[PROBE][P5] CurrentDepth before SaveChanges(): {depth_before_save}")

            _, save_exc_msg = _safe(project.SaveChanges, "P5 SaveChanges() while envelope still open")

            depth_after_save = _safe(lambda: _depth(project), "P5 CurrentDepth after SaveChanges()")[0]
            print(f"[PROBE][P5] CurrentDepth after SaveChanges() attempt: {depth_after_save}")

            # This End call now ends the GENUINELY still-open envelope (the
            # guard never touched it) -- no longer "forcing" a double-end onto
            # an already-collapsed one, as it did pre-guard.
            _, end_exc_msg = _safe(project.project.MainCacheAccessor.EndNonUndoableTask, "P5 manual EndNonUndoableTask (post-SaveChanges)")

            _, close_exc_msg = _safe(project.CloseProject, "P5 CloseProject (expected to succeed, guard finds envelope already ended)")
        finally:
            _dispose_if_open(project, "P5")

    # THE HEADLINE T8b ASSERTIONS: SaveChanges() must refuse with
    # FP_TransactionError, the raw liblcm string must NOT reach the caller,
    # and usm.Save() must never have been reached -- proven by CurrentDepth
    # staying UNCHANGED across the refused call (the guard reads depth but
    # never mutates LCM state).
    assert save_exc_msg is not None, (
        "SaveChanges() did not raise while CurrentDepth > 0 -- the issue "
        "#243 depth guard (spec.md C21) must refuse this call."
    )
    assert save_exc_msg.startswith("FP_TransactionError:"), (
        f"Expected the depth guard's FP_TransactionError; got: {save_exc_msg!r}"
    )
    assert "Commit at wrong place." not in save_exc_msg, (
        "The raw liblcm exception string must NO LONGER reach the caller "
        f"here -- the guard refuses before usm.Save() is ever attempted; "
        f"got: {save_exc_msg!r}"
    )
    assert depth_after_save == depth_before_save == 1, (
        f"Expected CurrentDepth to stay UNCHANGED at 1 across the refused "
        f"SaveChanges() call -- proof usm.Save() was never reached (the "
        f"guard reads CurrentDepth but never mutates LCM state); measured "
        f"before={depth_before_save}, after={depth_after_save}."
    )
    print(f"[PROBE][P5] SaveChanges() now refuses BEFORE usm.Save() (T8b): {save_exc_msg}")

    # The manual End now succeeds (envelope was genuinely still open --
    # unlike the pre-guard record where this same call found nothing to
    # end).
    assert end_exc_msg is None, (
        f"Expected the manual EndNonUndoableTask() to succeed against the "
        f"genuinely-still-open envelope (T8b left it untouched); got: "
        f"{end_exc_msg!r}. If this fails, SaveChanges()'s guard is "
        "mutating LCM state before refusing, which contradicts the "
        "fail-fast design."
    )

    assert close_exc_msg is None, (
        f"CloseProject() raised even though the envelope was already ended "
        f"above: {close_exc_msg!r} -- the guard should have found "
        "HasOpenSessionTask() False, skipped EndNonUndoableTask(), and "
        "still reached usm.Save()."
    )

    # T7 (spec.md C18/C23): CloseProject() must name the anomaly at ERROR
    # level -- this run's manual End above already closed the envelope, so
    # CloseProject() enters the "else:" branch. Pin that the record fires,
    # at the right level, naming HasOpenSessionTask() reading False, and
    # QUOTE it verbatim so the evidence file does not paraphrase.
    anomaly_records = [r for r in caplog.records if "HasOpenSessionTask() read False" in r.message]
    print(f"[PROBE][P5] anomaly ERROR records logged (expected 1): {len(anomaly_records)}")
    for r in anomaly_records:
        print(f"[PROBE][P5] ERROR record: level={r.levelname} message={r.getMessage()!r}")
    assert len(anomaly_records) == 1, (
        "Expected exactly one T7 anomaly ERROR record from CloseProject() "
        f"(the manual End above already closed the envelope); found "
        f"{len(anomaly_records)}: {[r.message for r in anomaly_records]}"
    )
    anomaly_record = anomaly_records[0]
    assert anomaly_record.levelname == "ERROR", (
        f"T7's anomaly log must be at ERROR level (spec.md C23); got "
        f"{anomaly_record.levelname}."
    )
    rendered = anomaly_record.getMessage()
    assert "unreachable by construction" in rendered, (
        f"Expected the anomaly message to name the anomaly as unreachable "
        f"by construction; got: {rendered!r}"
    )
    assert "usm.Save()" in rendered and "proceeding" in rendered, (
        f"Expected the anomaly message to state plainly that usm.Save() is "
        f"proceeding anyway; got: {rendered!r}"
    )
    assert "lost" not in rendered.lower(), (
        f"T7's anomaly message must assert NOTHING about whether data was "
        f"lost (spec.md C23); got: {rendered!r}"
    )
    assert "nothing pending to save" not in rendered.lower(), (
        "The pre-Save() HasUnsavedChanges diagnostic must never be worded "
        f"as 'nothing pending to save' (spec.md C18, proven false-negative "
        f"by P-9); got: {rendered!r}"
    )

    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        surviving_count = _count_prefixed_entries(reopen_project, prefix)
        print(f"[PROBE][P5] TEST_ entries surviving, re-read from LCM: {surviving_count} / {N_ENTRIES}")
    finally:
        _safe(reopen_project.CloseProject, "P5 reopen CloseProject")
        _dispose_if_open(reopen_project, "P5 reopen")

    # CHANGED by T8b: this is a MEASURED survivor count, not an assumption.
    # PREDICTED N_ENTRIES/N_ENTRIES (see docstring); the change set was
    # never touched by a failed commit attempt this time, so it should
    # commit normally via the manual End + CloseProject()'s usm.Save().
    if surviving_count == N_ENTRIES:
        verdict = (
            f"{surviving_count}/{N_ENTRIES} survived -- MATCHES the T8b "
            "prediction: SaveChanges()'s guard never touched the envelope "
            "or the change set, the manual End committed it normally, and "
            "CloseProject() persisted it at a legal depth."
        )
    elif surviving_count == 0:
        verdict = (
            f"0/{N_ENTRIES} survived -- CONTRADICTS the T8b prediction. "
            "This is a P0 FINDING, reported verbatim rather than tuned to "
            "match: the guard was expected to leave the change set intact "
            "for a normal End+Save, but the data did not survive."
        )
    else:
        verdict = (
            f"{surviving_count}/{N_ENTRIES} survived -- PARTIAL WRITE, "
            "itself P0-severity. Reported here, not papered over."
        )
    print(f"[PROBE][P5] GO/NO-GO VERDICT (T8b guard, measured not assumed): {verdict}")

    # Headline evidence artifact for T8b -- the exact measured count is
    # asserted (not merely "in {0, N_ENTRIES}") so a partial-write
    # regression cannot pass silently. If this assertion fails, DO NOT
    # retune it to the observed value -- report the discrepancy verbatim
    # as a P0 finding; per the task brief this is the acceptance test for
    # the owner's real sequence.
    assert surviving_count == N_ENTRIES, (
        f"Measured {surviving_count}/{N_ENTRIES} survivors for the P-5 "
        f"sequence under the T8b SaveChanges() depth guard; PREDICTED "
        f"{N_ENTRIES}/{N_ENTRIES} (the guard leaves the envelope and "
        "change set untouched, so the manual End + CloseProject() should "
        "commit and persist normally). If this assertion is failing, "
        "report the measured count as a P0 finding -- do not silently "
        "adjust this assertion to match."
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

@pytest.mark.requires_live_project
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

    T8b note: since the SaveChanges() depth guard landed, the public
    ``FLExProject.SaveChanges()`` refuses outright at CurrentDepth > 0
    (raises FP_TransactionError before usm.Save() is ever attempted), so it
    can no longer be used to trigger the raw liblcm no-op-commit mechanism
    this probe exists to characterise. This probe therefore calls the raw
    ``usm.Save()`` accessor directly -- the exact same accessor
    ``SaveChanges()`` uses internally -- so it keeps measuring the same
    liblcm mechanism unchanged by the guard. The guard only stops users
    reaching this path through the public API; it does not change what
    happens when liblcm's own commit path is reached directly.
    """
    from flexicon.code.FLExProject import FLExProject
    from SIL.LCModel import IUndoStackManager

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

        # Raw usm.Save() (see T8b note in docstring): the public
        # SaveChanges() now refuses first, so we reach liblcm's commit path
        # directly, the same way SaveChanges() does internally.
        usm = project.ObjectRepository(IUndoStackManager)
        _, save_exc_msg = _safe(usm.Save, "P7 raw usm.Save() while envelope still open")
        assert save_exc_msg is not None and "Commit at wrong place." in save_exc_msg, (
            f"Expected usm.Save() to raise the owner's exact symptom "
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

@pytest.mark.requires_live_project
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

    T8b note: since the SaveChanges() depth guard landed, the public
    ``FLExProject.SaveChanges()`` refuses outright at CurrentDepth > 0
    (raises FP_TransactionError before usm.Save() is ever attempted), so it
    can no longer be used to trigger the raw liblcm no-op-commit mechanism
    this probe exists to characterise. This probe therefore calls the raw
    ``usm.Save()`` accessor directly -- the exact same accessor
    ``SaveChanges()`` uses internally -- so it keeps measuring the same
    liblcm mechanism unchanged by the guard.
    """
    from flexicon.code.FLExProject import FLExProject
    from SIL.LCModel import IUndoStackManager

    fwdata_path = pathlib.Path(target_sandbox_path)
    setup_prefix = f"{TEST_PREFIX}p8setup_"
    fresh_prefix = f"{TEST_PREFIX}p8fresh_"

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    close_exc_msg = None
    try:
        created = _create_test_entries(project, setup_prefix, N_ENTRIES)
        print(f"[PROBE][P8] created {len(created)} setup entries with prefix {setup_prefix!r}")

        # Raw usm.Save() (see T8b note in docstring): the public
        # SaveChanges() now refuses first, so we reach liblcm's commit path
        # directly, the same way SaveChanges() does internally.
        usm = project.ObjectRepository(IUndoStackManager)
        _, save_exc_msg = _safe(usm.Save, "P8 raw usm.Save() while envelope still open")
        assert save_exc_msg is not None and "Commit at wrong place." in save_exc_msg, (
            f"Expected usm.Save() to raise the owner's exact symptom "
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

@pytest.mark.requires_live_project
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

    Both shapes call usm.Save() manually from the test (directly, via the
    raw ObjectRepository(IUndoStackManager) accessor -- see the T8b note
    below) rather than only through CloseProject() -- this is what lets the
    test read the detector on BOTH sides of the exact call, and it changes
    no flexicon/ code: CloseProject() is still called, unmodified, to
    finish each project's lifecycle.

    T8b note: since the SaveChanges() depth guard landed, the public
    ``FLExProject.SaveChanges()`` refuses outright at CurrentDepth > 0
    (raises FP_TransactionError before usm.Save() is ever attempted), so
    the TRIGGER call below can no longer reach liblcm's raw commit path
    through SaveChanges(). Both the TRIGGER call and the second (no-op)
    call in the no-op shape now go through the raw ``usm.Save()`` accessor
    directly -- the exact same accessor ``SaveChanges()`` uses internally
    -- so this probe keeps measuring the same liblcm mechanism unchanged
    by the guard.

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
            detector_before_trigger = _safe(lambda: usm.HasUnsavedChanges, "P9 HasUnsavedChanges before TRIGGER usm.Save()")[0]
        print(f"[PROBE][P9] (no-op shape) HasUnsavedChanges before the TRIGGER usm.Save(): {detector_before_trigger}")

        # Raw usm.Save() (see T8b note in docstring): the public
        # SaveChanges() now refuses first, so we reach liblcm's commit path
        # directly, the same way SaveChanges() does internally.
        _, save_exc_msg = _safe(usm.Save, "P9 TRIGGER raw usm.Save() while envelope still open")
        assert save_exc_msg is not None and "Commit at wrong place." in save_exc_msg, (
            f"Expected the TRIGGER usm.Save() to raise the owner's exact "
            f"symptom string; got: {save_exc_msg!r}"
        )

        if has_detector:
            detector_after_trigger = _safe(lambda: usm.HasUnsavedChanges, "P9 HasUnsavedChanges after TRIGGER usm.Save()")[0]
        print(f"[PROBE][P9] (no-op shape) HasUnsavedChanges after the TRIGGER usm.Save() raised: {detector_after_trigger}")

        _safe(project.project.MainCacheAccessor.EndNonUndoableTask, "P9 forced manual EndNonUndoableTask (post-trigger)")
        depth_before_noop_save = _safe(lambda: _depth(project), "P9 CurrentDepth before the no-op Save()")[0]
        print(f"[PROBE][P9] (no-op shape) CurrentDepth before the no-op Save(): {depth_before_noop_save}")

        if has_detector:
            detector_before_noop = _safe(lambda: usm.HasUnsavedChanges, "P9 HasUnsavedChanges immediately BEFORE the no-op usm.Save()")[0]
        print(f"[PROBE][P9] (no-op shape) HasUnsavedChanges BEFORE the no-op usm.Save(): {detector_before_noop}")

        # This SECOND call is the exact usm.Save() shape CloseProject()
        # reaches once the T3 guard skips the already-collapsed envelope's
        # End -- same `usm` object, same depth (0). Calling it directly
        # here (rather than via CloseProject(), and via the raw accessor
        # rather than SaveChanges() -- T8b note above) is what lets this
        # test read the detector on both sides of exactly that call. At
        # depth 0 the SaveChanges() guard would not fire anyway, but the
        # raw call is used here for consistency with the TRIGGER call
        # above.
        _, noop_save_exc_msg = _safe(usm.Save, "P9 NO-OP raw usm.Save() (mirrors CloseProject()'s guarded usm.Save())")
        print(f"[PROBE][P9] (no-op shape) second usm.Save() call raised: {noop_save_exc_msg}")

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


# ===========================================================================
# P-10 -- SaveChanges() DEPTH BLAST RADIUS: THE UndoableOperation()/
# Transaction() CASES (T8a, measurement only -- no flexicon/ file touched)
#
# This does NOT modify SaveChanges() or CloseProject(). It measures the one
# case the frozen P-2/T1 depth table never exercised against SaveChanges():
# what SaveChanges() actually does at CurrentDepth == 1 reached via
# `with project.UndoableOperation(...)` under undoable=True, versus the
# already-understood undoable=False bare-session depth-1 case (P-5/P-7).
# Also re-verifies, by direct measurement rather than by citing the frozen
# P-2/T1 table, that `Transaction()` does not itself change CurrentDepth in
# either mode. This decides whether the guard approved for T8b can be a
# blanket `CurrentDepth > 0` refusal, or must be narrowed to spare a
# genuinely working edit.
# ===========================================================================

def _measure_savechanges_in_context(project, cm_factory, case_label, prefix):
    """
    Create N_ENTRIES TEST_-prefixed entries, then call SaveChanges() from
    inside the context manager `cm_factory()` returns, recording:
      (2) CurrentDepth immediately BEFORE SaveChanges(),
      (3) whether SaveChanges() raised, and the verbatim message if so,
      (4) CurrentDepth immediately AFTER,
      (5) the survivor count re-read from the LCM on the STILL-OPEN
          project (P-7 technique), taken BEFORE the context manager's own
          __exit__ runs, so the measurement isolates SaveChanges() itself
          from whatever the block's own exit-time commit/rollback logic
          does.
    Uses _safe() around the SaveChanges() call specifically so any raised
    exception is caught there and never propagates to the `with` block's
    __exit__ -- a genuinely transactional block (UndoableOperation()) would
    otherwise treat an escaping exception as a rollback trigger for
    everything inside it, which would conflate "what SaveChanges() did" with
    "what the block did in response to an unrelated failure."
    Item (6) -- on-disk survival after a genuine close/reopen -- is measured
    by the caller once every case's project has actually been closed.
    """
    created = _create_test_entries(project, prefix, N_ENTRIES)
    print(f"[PROBE][P10] ({case_label}) created {len(created)} entries with prefix {prefix!r}")

    with cm_factory():
        depth_before = _depth(project)
        print(f"[PROBE][P10] ({case_label}) CurrentDepth before SaveChanges(): {depth_before}")

        _, save_exc_msg = _safe(project.SaveChanges, f"P10 ({case_label}) SaveChanges()")

        depth_after = _safe(lambda: _depth(project), f"P10 ({case_label}) CurrentDepth after SaveChanges()")[0]
        print(f"[PROBE][P10] ({case_label}) CurrentDepth after SaveChanges(): {depth_after}")

        in_memory_count = _count_prefixed_entries(project, prefix)
        print(
            f"[PROBE][P10] ({case_label}) survivor count re-read from the "
            f"STILL-OPEN project (inside the block, before its __exit__): "
            f"{in_memory_count} / {N_ENTRIES}"
        )

    return {
        "case": case_label,
        "depth_before": depth_before,
        "save_exc_msg": save_exc_msg,
        "depth_after": depth_after,
        "in_memory_count": in_memory_count,
    }


@pytest.mark.requires_live_project
@pytest.mark.live_phase("FLExProject", "modify")
def test_p10_savechanges_depth_blast_radius(target_sandbox_path):
    """
    T8a / P-10 (measurement only): three cases, none of them previously
    measured against SaveChanges() directly.

    - Case A: undoable=True, SaveChanges() called INSIDE
      `with project.UndoableOperation(...)`. Per the frozen P-2/T1 table
      (test_p2_public_surface_matches_depth_table, row
      "undoable_operation_block"), CurrentDepth is 1 there -- this is the
      one case named in the task as never measured against SaveChanges().
      This case decides the guard's shape: if SaveChanges() raises here and
      destroys the change set (like the undoable=False bare-session case),
      a blanket `CurrentDepth > 0` refusal removes nothing that worked. If
      it SUCCEEDS and the edit persists, the same blanket guard would newly
      refuse a WORKING edit made through FLExProject's own recommended
      undoable-mode API, which the owner's ruling forbids.

      MEASURED LIVE (spurt 6, T8a, 2026-09-07): a THIRD outcome, distinct
      from both of the above -- SaveChanges() RAISES the identical
      "Commit at wrong place." string (same as the undoable=False
      mechanism), CurrentDepth collapses 1 -> 0 as the same side effect,
      YET the change set is NOT destroyed: 25/25 survive re-read from the
      STILL-OPEN project (before the block's own __exit__ runs) AND 25/25
      survive a genuine close-and-reopen. The data's survival does not
      depend on this SaveChanges() call succeeding at all -- it is
      registered onto the real UndoableUnitOfWorkHelper stack by the
      UndoableOperation() block's own normal (non-exceptional) __exit__,
      and is then captured for real by CloseProject()'s own later
      usm.Save() at the now-legal depth 0. Consequence for the guard: a
      blanket `CurrentDepth > 0` refusal changes NOTHING about this case's
      outcome -- the call already fails today (just with LCM's cryptic
      message instead of the guard's own), and the edit was never actually
      at risk from this specific call one way or the other. See the
      "CASE A VERDICT" print block below for the reasoning pinned as a
      named branch, not folded into a generic partial-write catch-all.
    - Case B: undoable=True, SaveChanges() called INSIDE
      `with project.Transaction(...)`. Per the same frozen table
      ("transaction_block_undoable_true"), CurrentDepth is 0 there, matching
      the bare undoable=True session -- this case re-verifies, by direct
      measurement here rather than by citing that table, that `Transaction()`
      does not itself change CurrentDepth.
    - Case C: undoable=False, SaveChanges() called INSIDE
      `with project.Transaction(...)`. Per the same frozen table
      ("transaction_block_undoable_false"), CurrentDepth is 1 there, matching
      the bare undoable=False session (P-5/P-7) -- re-verified here directly,
      not assumed.

    Depth-before setup-sanity assertions pin the frozen P-2/T1 table values
    for these three rows; if any of them fails, the underlying depth
    behaviour has CHANGED since T1 and must be reported, not silently
    re-baselined.

    No file under flexicon/ is touched BY THIS TEST: SaveChanges() and
    CloseProject() are only ever called through FLExProject's own public
    API, exactly as an application would call them.

    T8B UPDATE (spurt 7, 2026-09-07): this test now runs AGAINST the
    SaveChanges() depth guard landed by T8b (spec.md C21), not the
    pre-guard code the T8a measurements above describe. The guard reads
    CurrentDepth and refuses with FP_TransactionError BEFORE usm.Save() is
    ever attempted, whenever CurrentDepth > 0 -- so for Case A and Case C
    (both depth 1) the exception type and message change (FP_TransactionError,
    not the raw "Commit at wrong place." liblcm string), and CurrentDepth is
    no longer collapsed as a side effect (the guard never touches LCM
    state, so depth_after == depth_before == 1 for both). Case B (depth 0)
    is untouched -- the guard never fires there.

    The DATA outcome differs between the two depth-1 cases, and this is the
    reason a blanket guard was ruled SAFE (T8a's finding, unchanged):
    - Case A (UndoableOperation(), undoable=True): data outcome UNCHANGED
      at 25/25 both reads. It never depended on this specific SaveChanges()
      call succeeding -- the UndoableOperation() block's own normal
      __exit__ commits the edit onto the real undo stack regardless, and
      CloseProject() persists it. The guard refusing earlier (with a
      clearer message) sacrifices nothing that worked before.
    - Case C (Transaction(), undoable=False): data outcome CHANGES from the
      T8a-measured 0/25 (both reads) to a PREDICTED 25/25 (both reads).
      Under the old, unguarded liblcm mechanism, SaveChanges() actually
      called usm.Save(), which failed AND discarded the pending change set
      as a measured side effect (C16 mechanism (ii)/(iii)). The T8b guard
      never calls usm.Save() at all, so that discard never happens: the
      change set stays intact and registered against the still-open
      session-long envelope, Transaction()'s own exit is a no-op in this
      mode (no rollback capability -- see transaction.py's _FLExTransaction
      docstring), and CloseProject() reaches an intact change set at a
      legal depth. MEASURE, do not assume -- if this prediction is wrong,
      report the measured values verbatim as a P0 finding.
    """
    from flexicon.code.FLExProject import FLExProject

    fwdata_path = pathlib.Path(target_sandbox_path)
    cases = []  # list of (result_dict, close_exc_msg, prefix)

    # --- Case A: undoable=True, inside UndoableOperation() ---
    prefix_a = f"{TEST_PREFIX}p10a_"
    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=True)
    close_exc_msg_a = None
    try:
        result_a = _measure_savechanges_in_context(
            project,
            lambda: project.UndoableOperation("p10 probe"),
            "A: undoable=True, inside UndoableOperation()",
            prefix_a,
        )
        _, close_exc_msg_a = _safe(project.CloseProject, "P10 case A CloseProject")
    finally:
        _dispose_if_open(project, "P10 case A")
    cases.append((result_a, close_exc_msg_a, prefix_a))

    # --- Case B: undoable=True, inside Transaction() ---
    prefix_b = f"{TEST_PREFIX}p10b_"
    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=True)
    close_exc_msg_b = None
    try:
        result_b = _measure_savechanges_in_context(
            project,
            lambda: project.Transaction("p10 probe"),
            "B: undoable=True, inside Transaction()",
            prefix_b,
        )
        _, close_exc_msg_b = _safe(project.CloseProject, "P10 case B CloseProject")
    finally:
        _dispose_if_open(project, "P10 case B")
    cases.append((result_b, close_exc_msg_b, prefix_b))

    # --- Case C: undoable=False, inside Transaction() ---
    prefix_c = f"{TEST_PREFIX}p10c_"
    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=False)
    close_exc_msg_c = None
    try:
        result_c = _measure_savechanges_in_context(
            project,
            lambda: project.Transaction("p10 probe"),
            "C: undoable=False, inside Transaction()",
            prefix_c,
        )
        _, close_exc_msg_c = _safe(project.CloseProject, "P10 case C CloseProject")
    finally:
        _dispose_if_open(project, "P10 case C")
    cases.append((result_c, close_exc_msg_c, prefix_c))

    # --- Item (6) for all three cases: on-disk survival after a genuine
    # close-and-reopen. One shared reopen, three counts. ---
    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        for result, _close_exc_msg, prefix in cases:
            on_disk_count = _count_prefixed_entries(reopen_project, prefix)
            result["on_disk_count"] = on_disk_count
            print(
                f"[PROBE][P10] ({result['case']}) survivor count after a "
                f"genuine close-and-reopen: {on_disk_count} / {N_ENTRIES}"
            )
    finally:
        _safe(reopen_project.CloseProject, "P10 reopen CloseProject")
        _dispose_if_open(reopen_project, "P10 reopen")

    # --- Full six-item table, one line per case, for the evidence file. ---
    for result, close_exc_msg, _prefix in cases:
        print(
            f"[PROBE][P10] TABLE {result['case']}: "
            f"depth_before={result['depth_before']}, "
            f"save_raised={result['save_exc_msg']!r}, "
            f"depth_after={result['depth_after']}, "
            f"in_memory_count={result['in_memory_count']}/{N_ENTRIES}, "
            f"on_disk_count={result['on_disk_count']}/{N_ENTRIES}, "
            f"CloseProject_raised={close_exc_msg!r}"
        )

    # --- Setup sanity: CloseProject() itself must not raise in any of the
    # three cases (this probe only measures SaveChanges(), not
    # CloseProject() -- a raise here would mean the probe's own scaffolding
    # is broken, not a new finding about the guard). ---
    for result, close_exc_msg, _prefix in cases:
        assert close_exc_msg is None, (
            f"CloseProject() raised unexpectedly for case {result['case']}: "
            f"{close_exc_msg!r} -- this probe only measures SaveChanges(), "
            "so a raise here means the probe scaffolding itself is broken."
        )

    # --- Setup sanity: pin the frozen P-2/T1 CurrentDepth values for these
    # three rows (test_p2_public_surface_matches_depth_table). If any of
    # these fail, the underlying depth behaviour has CHANGED since T1. ---
    assert result_a["depth_before"] == 1, (
        f"Expected CurrentDepth == 1 inside UndoableOperation() under "
        f"undoable=True (frozen P-2/T1 row 'undoable_operation_block'); "
        f"got {result_a['depth_before']}."
    )
    assert result_b["depth_before"] == 0, (
        f"Expected CurrentDepth == 0 inside Transaction() under "
        f"undoable=True (frozen P-2/T1 row 'transaction_block_undoable_true'); "
        f"got {result_b['depth_before']}. Transaction() would no longer be "
        "depth-neutral in undoable=True mode -- report this, do not assume."
    )
    assert result_c["depth_before"] == 1, (
        f"Expected CurrentDepth == 1 inside Transaction() under "
        f"undoable=False (frozen P-2/T1 row 'transaction_block_undoable_false'); "
        f"got {result_c['depth_before']}. Transaction() would no longer be "
        "depth-neutral in undoable=False mode -- report this, do not assume."
    )

    # --- Headline verdict, printed for the evidence file. Deliberately NOT
    # hard-coding an assumed outcome for case A beyond what is asserted
    # below on the MEASURED values -- that is the entire point of this
    # probe: find out, don't guess. ---
    print(
        "[PROBE][P10] VERDICT: "
        f"A(UndoableOperation,undoable=True,depth=1): "
        f"SaveChanges() {'RAISED' if result_a['save_exc_msg'] else 'SUCCEEDED'}, "
        f"in_memory={result_a['in_memory_count']}/{N_ENTRIES}, "
        f"on_disk={result_a['on_disk_count']}/{N_ENTRIES} || "
        f"B(Transaction,undoable=True,depth=0): "
        f"SaveChanges() {'RAISED' if result_b['save_exc_msg'] else 'SUCCEEDED'}, "
        f"in_memory={result_b['in_memory_count']}/{N_ENTRIES}, "
        f"on_disk={result_b['on_disk_count']}/{N_ENTRIES} || "
        f"C(Transaction,undoable=False,depth=1): "
        f"SaveChanges() {'RAISED' if result_c['save_exc_msg'] else 'SUCCEEDED'}, "
        f"in_memory={result_c['in_memory_count']}/{N_ENTRIES}, "
        f"on_disk={result_c['on_disk_count']}/{N_ENTRIES}"
    )

    # --- Case B control assertion: MEASURED, not assumed. Depth-0, so the
    # T8b guard never fires -- expected to behave exactly like the
    # already-understood bare undoable=True case (SaveChanges() succeeds,
    # edit persists). Asserted on the measured value so a future change to
    # this mechanism is caught here, not silently re-baselined. ---
    assert result_b["save_exc_msg"] is None, (
        f"Case B (Transaction(), undoable=True, depth=0) was expected to "
        f"match the bare undoable=True case and SUCCEED; SaveChanges() "
        f"raised instead: {result_b['save_exc_msg']!r}. This is a NEW "
        "finding if it reproduces -- report it, do not loosen this "
        "assertion to match."
    )
    assert result_b["on_disk_count"] == N_ENTRIES, (
        f"Case B (Transaction(), undoable=True, depth=0) was expected to "
        f"persist all {N_ENTRIES} entries; got "
        f"{result_b['on_disk_count']}/{N_ENTRIES}."
    )
    assert result_b["depth_after"] == 0, (
        f"Case B (Transaction(), undoable=True, depth=0) was expected to "
        f"leave CurrentDepth unchanged at 0 (SaveChanges() succeeded "
        f"normally, no guard involvement); got {result_b['depth_after']}."
    )

    # --- Case C: CHANGED by T8b (spec.md C21). Under the guard,
    # SaveChanges() refuses BEFORE usm.Save() is ever attempted, so the raw
    # liblcm "Commit at wrong place." string no longer reaches the caller,
    # CurrentDepth is left UNCHANGED (proof usm.Save() was never reached --
    # the guard reads depth but never mutates LCM state), and the pending
    # change set -- never touched by a failed commit attempt this time --
    # is PREDICTED to survive intact through CloseProject()'s own later
    # usm.Save(). MEASURE, do not assume: if any of this is wrong, report
    # the measured values verbatim as a P0 finding rather than adjusting
    # these assertions to match. ---
    assert result_c["save_exc_msg"] is not None, (
        "Case C (Transaction(), undoable=False, depth=1) was expected to "
        "raise the T8b depth guard's FP_TransactionError; SaveChanges() "
        "did not raise at all."
    )
    assert result_c["save_exc_msg"].startswith("FP_TransactionError:"), (
        f"Case C (Transaction(), undoable=False, depth=1) was expected to "
        f"raise FP_TransactionError from the T8b depth guard; got "
        f"{result_c['save_exc_msg']!r}."
    )
    assert "Commit at wrong place." not in result_c["save_exc_msg"], (
        f"Case C's raw liblcm exception string must NO LONGER reach the "
        f"caller -- the guard refuses before usm.Save() is ever attempted; "
        f"got: {result_c['save_exc_msg']!r}."
    )
    assert result_c["depth_after"] == result_c["depth_before"] == 1, (
        f"Case C (Transaction(), undoable=False, depth=1) was expected to "
        f"leave CurrentDepth UNCHANGED at 1 across the refused "
        f"SaveChanges() call -- proof usm.Save() was never reached; "
        f"measured before={result_c['depth_before']}, "
        f"after={result_c['depth_after']}."
    )
    assert result_c["in_memory_count"] == N_ENTRIES, (
        f"Case C (Transaction(), undoable=False, depth=1): PREDICTED "
        f"{N_ENTRIES}/{N_ENTRIES} still visible in the STILL-OPEN project "
        f"immediately after the guard refused SaveChanges() (the change "
        f"set was never touched by a failed commit attempt this time); "
        f"got {result_c['in_memory_count']}/{N_ENTRIES}. If this fails, "
        "report the measured count as a P0 finding -- do not silently "
        "adjust this assertion to match."
    )
    assert result_c["on_disk_count"] == N_ENTRIES, (
        f"Case C (Transaction(), undoable=False, depth=1): PREDICTED "
        f"{N_ENTRIES}/{N_ENTRIES} survivors after a genuine reopen (the "
        f"intact change set commits normally via CloseProject()'s own "
        f"End + usm.Save()); got {result_c['on_disk_count']}/{N_ENTRIES}. "
        "If this fails, report the measured count as a P0 finding -- do "
        "not silently adjust this assertion to match."
    )

    # --- Case A: THE headline unmeasured case. Pin whatever was actually
    # measured live so this cannot silently regress or be re-baselined
    # without visibly failing. MEASURED LIVE, do not adjust without
    # reporting the new numbers per the task's binding evidence rules.
    #
    # If SaveChanges() SUCCEEDED and the edit persisted (on_disk ==
    # N_ENTRIES): a blanket `CurrentDepth > 0` refusal on SaveChanges()
    # WOULD sacrifice a genuinely working edit in this case, and the guard
    # approved for T8b must be narrowed to exclude it (e.g. distinguish via
    # HasOpenSessionTask()'s own undoable-mode-aware semantics, or some
    # other signal that separates a UndoableOperation()-owned depth-1 from
    # the bare undoable=False session-long depth-1).
    #
    # If SaveChanges() RAISED and the edit was destroyed (on_disk == 0,
    # matching the undoable=False mechanism exactly): a blanket
    # `CurrentDepth > 0` refusal removes nothing that worked, and is SAFE
    # as far as this case is concerned.
    if result_a["save_exc_msg"] is None and result_a["on_disk_count"] == N_ENTRIES:
        print(
            "[PROBE][P10] CASE A VERDICT: SaveChanges() SUCCEEDED and the "
            "edit PERSISTED to disk at CurrentDepth == 1 inside "
            "UndoableOperation() under undoable=True. A blanket "
            "`CurrentDepth > 0` guard on SaveChanges() WOULD SACRIFICE THIS "
            "WORKING EDIT and must be narrowed for T8b."
        )
    elif result_a["save_exc_msg"] is not None and result_a["on_disk_count"] == 0:
        print(
            "[PROBE][P10] CASE A VERDICT: SaveChanges() RAISED and the edit "
            "was DESTROYED (0/{N_ENTRIES} on disk), matching the "
            "undoable=False bare-session mechanism exactly. A blanket "
            "`CurrentDepth > 0` guard removes nothing that worked here."
        )
    elif result_a["save_exc_msg"] is not None and result_a["on_disk_count"] == N_ENTRIES:
        print(
            "[PROBE][P10] CASE A VERDICT (MEASURED, third outcome -- "
            "distinct from both named alternatives above; T8b UPDATE: "
            "the exception is now the guard's own FP_TransactionError, "
            "raised BEFORE usm.Save() is ever attempted, not the raw "
            "liblcm 'Commit at wrong place.' string T8a measured): "
            "SaveChanges() RAISED, YET the edit was NOT destroyed -- "
            "25/25 survived in-memory (still-open, before the block's own "
            "__exit__) AND 25/25 survived a genuine close-and-reopen. The "
            "survival does not depend on this SaveChanges() call: the "
            "UndoableOperation() block's own normal __exit__ (no exception "
            "escaped, because _safe() caught it) commits the edit onto the "
            "real UndoableUnitOfWorkHelper stack regardless, and "
            "CloseProject()'s own later usm.Save() at the now-legal depth "
            "0 persists it for real. VERDICT: BLANKET GUARD SAFE for this "
            "case -- the call already failed before T8b too (just with "
            "LCM's cryptic message instead of the guard's own clearer "
            "one), and the edit was never actually at risk from this "
            "specific SaveChanges() call one way or the other, so "
            "refusing it earlier sacrifices nothing."
        )
    else:
        print(
            f"[PROBE][P10] CASE A VERDICT: PARTIAL/UNEXPECTED result -- "
            f"save_raised={bool(result_a['save_exc_msg'])}, "
            f"in_memory={result_a['in_memory_count']}/{N_ENTRIES}, "
            f"on_disk={result_a['on_disk_count']}/{N_ENTRIES}. Does not "
            "match any of the three named outcomes above; report exactly "
            "as measured, this is itself P0-severity information for the "
            "guard's shape."
        )

    # --- Pin the exact measured Case A result as a regression lock,
    # mirroring the P-5/P-7/P-8/P-9 "assert the MEASURED value, not the
    # hoped-for one" convention. If this fails, Case A's behaviour has
    # CHANGED since this spurt -- report the new numbers, do not silently
    # adjust this assertion to match. UPDATED for T8b: the exception type
    # and depth-after value change (guard refuses before usm.Save(), never
    # mutating LCM state); the data outcome (25/25 both reads) does not. ---
    assert result_a["save_exc_msg"] is not None, (
        "Case A (UndoableOperation(), undoable=True, depth=1) was expected "
        "to raise the T8b depth guard's FP_TransactionError; SaveChanges() "
        "did not raise at all."
    )
    assert result_a["save_exc_msg"].startswith("FP_TransactionError:"), (
        f"MEASURED LIVE: Case A (UndoableOperation(), undoable=True, "
        f"depth=1) was expected to raise the T8b guard's "
        f"FP_TransactionError; got {result_a['save_exc_msg']!r} instead. "
        "This is a CHANGE from the recorded finding -- report it."
    )
    assert "Commit at wrong place." not in result_a["save_exc_msg"], (
        f"Case A's raw liblcm exception string must NO LONGER reach the "
        f"caller -- the guard refuses before usm.Save() is ever attempted; "
        f"got: {result_a['save_exc_msg']!r}."
    )
    assert result_a["depth_after"] == result_a["depth_before"] == 1, (
        f"Case A (UndoableOperation(), undoable=True, depth=1) was "
        f"expected to leave CurrentDepth UNCHANGED at 1 across the refused "
        f"SaveChanges() call -- proof usm.Save() was never reached; "
        f"measured before={result_a['depth_before']}, "
        f"after={result_a['depth_after']}."
    )
    assert result_a["in_memory_count"] == N_ENTRIES, (
        f"MEASURED LIVE (spurt 6, T8a): Case A's edit survived in-memory "
        f"({N_ENTRIES}/{N_ENTRIES}) despite SaveChanges() raising; got "
        f"{result_a['in_memory_count']}/{N_ENTRIES}. This is a CHANGE from "
        "the recorded finding -- report it, this is the exact measurement "
        "the guard's shape decision depends on."
    )
    assert result_a["on_disk_count"] == N_ENTRIES, (
        f"MEASURED LIVE (spurt 6, T8a): Case A's edit survived a genuine "
        f"close-and-reopen ({N_ENTRIES}/{N_ENTRIES}) despite SaveChanges() "
        f"raising; got {result_a['on_disk_count']}/{N_ENTRIES}. This is a "
        "CHANGE from the recorded finding -- report it, this is the exact "
        "measurement the guard's shape decision depends on."
    )


# ===========================================================================
# P-11 -- CASE A, BUT LET THE GUARD'S EXCEPTION PROPAGATE (T8b, spec.md C21)
#
# P-10 case A deliberately isolated SaveChanges() from the block's own
# exit-time commit/rollback logic by catching the guard's exception with
# _safe() -- exactly so the measurement above answers "what does THIS CALL
# do" rather than "what does an unrelated escaping exception do to the
# block". This probe asks the complementary, equally real-world question:
# an application that does NOT catch SaveChanges()'s FP_TransactionError
# lets it propagate out of the `with project.UndoableOperation(...)` block,
# which (per _NestingAwareTransaction.__exit__, FLExProject.py's
# transaction.py) treats ANY escaping exception as a rollback trigger for
# the whole block, independent of what raised it.
#
# No file under flexicon/ is touched by this test. This does not modify
# SaveChanges(), UndoableOperation(), or CloseProject().
# ===========================================================================

@pytest.mark.requires_live_project
@pytest.mark.live_phase("FLExProject", "modify")
def test_p11_case_a_exception_propagates_and_rolls_back(target_sandbox_path):
    """
    T8b / P-11 (spec.md C21, task brief "NEW: P-11"): P-10 case A repeated,
    but this time the guard's FP_TransactionError is allowed to PROPAGATE
    out of the `with project.UndoableOperation(...)` block instead of being
    caught by _safe() inside it.

    Mechanism (per transaction.py's _NestingAwareTransaction.__exit__ and
    UndoableOperation()'s own docstring): an escaping exception makes the
    block's own UndoableUnitOfWorkHelper call `set_RollBack(True)` before
    Dispose(). This is NOT new behaviour introduced by the T8b guard: the
    same block already ran this same exit path on ANY escaping exception
    before the guard existed (e.g. the raw liblcm
    InvalidOperationException this same call used to raise, pre-T8b, if a
    caller ALSO did not catch it -- P-10 case A only avoided this outcome
    by deliberately catching it with _safe()).

    PREDICTED (a priori, before this probe was run): 0/25 survivors, on the
    assumption that `RollBack=True` discards every mutation made inside the
    block.

    MEASURED LIVE (spurt 7, T8b, 2026-09-07) -- CONTRADICTS THE PREDICTION,
    reported verbatim as a P0 FINDING rather than silently retuned: 25/25
    survivors, BOTH in-memory (re-read from the still-open project
    immediately after the block's exit, before CloseProject()) AND on-disk
    (after a genuine close-and-reopen). The debug log DOES confirm
    `set_RollBack(True)` and `Dispose()` ran ("UnitOfWork rolled back"), yet
    the 25 created entries were NOT discarded either time. This means
    `UndoableUnitOfWorkHelper.Dispose()` with `RollBack=True` does NOT, in
    this measured case, revert already-applied object creation the way its
    own naming and transaction.py's/undoable_operation.py's docstrings both
    assert it does. This is NOT the SaveChanges() depth guard's doing -- the
    guard raised and refused correctly (see the assertions above); this
    finding is about what liblcm's OWN rollback primitive does afterward,
    independent of what triggered the escape. Distinguishing exactly why
    (e.g. object creation may already be reflected in the cache's live
    collections in a way `RollBack` does not reach, as opposed to modified
    property values) needs instrumentation inside liblcm/UnitOfWorkHelper.cs
    and is OUT OF SCOPE for this task (same disposition as spec.md C16's
    "needs instrumentation inside liblcm" boundary) -- reported as a P0
    finding for /lex-lead to route, not investigated further here.

    THE BINDING CONSEQUENCE FOR THE T8b DOCSTRING (per the task brief): the
    undoable=True SaveChanges() docstring must not describe the escaping-
    exception outcome from inference, and it does not -- it only states that
    the block "commits automatically when it exits normally," which says
    nothing about what happens on a non-normal exit, so this measured
    surprise does not falsify anything the shipped docstring claims. But any
    FUTURE claim that "an escaping exception safely discards the edit" would
    be FALSE per this measurement and must not be written anywhere in this
    codebase without re-verifying first.
    """
    from flexicon.code.FLExProject import FLExProject
    from flexicon.code.exceptions import FP_TransactionError

    fwdata_path = pathlib.Path(target_sandbox_path)
    prefix = f"{TEST_PREFIX}p11_"

    project = FLExProject()
    project.OpenProject(str(fwdata_path), writeEnabled=True, undoable=True)
    close_exc_msg = None
    propagated_exc = None
    in_memory_count = None
    try:
        created = _create_test_entries(project, prefix, N_ENTRIES)
        print(f"[PROBE][P11] created {len(created)} entries with prefix {prefix!r}")

        depth_before_block = _depth(project)
        print(f"[PROBE][P11] CurrentDepth before UndoableOperation() block: {depth_before_block}")

        try:
            with project.UndoableOperation("p11 probe"):
                depth_inside = _depth(project)
                print(f"[PROBE][P11] CurrentDepth inside UndoableOperation() block: {depth_inside}")
                # Deliberately NOT wrapped in _safe() -- the whole point of
                # this probe is to let the raise ESCAPE the `with` block.
                project.SaveChanges()
        except FP_TransactionError as e:
            propagated_exc = e
            print(f"[PROBE][P11] FP_TransactionError PROPAGATED out of the "
                  f"UndoableOperation() block, as expected: {e}")

        depth_after_block = _safe(lambda: _depth(project), "P11 CurrentDepth after the block")[0]
        print(f"[PROBE][P11] CurrentDepth after the block's own rollback exit: {depth_after_block}")

        # THE MEASUREMENT: re-read from the STILL-OPEN in-memory project,
        # before CloseProject() is ever called (P-7 technique).
        in_memory_count = _count_prefixed_entries(project, prefix)
        print(
            f"[PROBE][P11] TEST_ entries still visible in the STILL-OPEN "
            f"project after the block rolled back: {in_memory_count} / {N_ENTRIES}"
        )

        _, close_exc_msg = _safe(project.CloseProject, "P11 CloseProject")
    finally:
        _dispose_if_open(project, "P11")

    assert propagated_exc is not None, (
        "SaveChanges() did not raise FP_TransactionError at all inside the "
        "UndoableOperation() block -- the depth guard should have fired "
        "(CurrentDepth == 1 inside the block, per the frozen P-2/T1 table)."
    )

    assert close_exc_msg is None, (
        f"CloseProject() raised unexpectedly: {close_exc_msg!r} -- this "
        "probe only measures the block's own rollback behaviour, so a "
        "raise here means the probe scaffolding itself is broken."
    )

    reopen_project = FLExProject()
    reopen_project.OpenProject(str(fwdata_path), writeEnabled=False)
    try:
        surviving_count = _count_prefixed_entries(reopen_project, prefix)
        print(f"[PROBE][P11] TEST_ entries surviving a genuine close-and-reopen: {surviving_count} / {N_ENTRIES}")
    finally:
        _safe(reopen_project.CloseProject, "P11 reopen CloseProject")
        _dispose_if_open(reopen_project, "P11 reopen")

    print(
        f"[PROBE][P11] VERDICT: FP_TransactionError propagated out of "
        f"UndoableOperation(), Dispose()/set_RollBack(True) ran (per the "
        f"debug log) -- in_memory={in_memory_count}/{N_ENTRIES}, "
        f"on_disk={surviving_count}/{N_ENTRIES}. "
        f"{'MATCHES the a-priori prediction (0/25).' if in_memory_count == 0 and surviving_count == 0 else 'P0 FINDING: CONTRADICTS the a-priori 0/25 rollback prediction -- RollBack(True)+Dispose() ran but did NOT discard the created entries. See docstring MEASURED LIVE section.'}"
    )

    # MEASURED LIVE (spurt 7, T8b, 2026-09-07) -- CONTRADICTS the a-priori
    # 0/25 prediction recorded in the docstring above. 25/25 survived both
    # reads despite the debug log confirming set_RollBack(True) + Dispose()
    # ran. This is asserted as the MEASURED value, per this file's own
    # established convention (P-5/P-7/P-8/P-9/P-10: "assert the MEASURED
    # value, not the hoped-for one") -- NOT silently retuned to make the
    # test green, but pinned so a FUTURE change to this liblcm mechanism is
    # caught here rather than re-surprising a future reader. Reported
    # prominently as a P0 finding in reviews/cycle7-programmer.md; the
    # SaveChanges() docstring does not claim otherwise (see docstring above)
    # so this is not a documentation contradiction, but it IS a live
    # liblcm-mechanism finding outside this task's scope to investigate
    # further (would need instrumentation inside UnitOfWorkHelper.cs).
    assert in_memory_count == N_ENTRIES, (
        f"MEASURED LIVE: {N_ENTRIES}/{N_ENTRIES} survivors in-memory despite "
        f"the escaping exception triggering set_RollBack(True) + Dispose() "
        f"on the UndoableOperation() block (CONTRADICTS the a-priori 0/25 "
        f"prediction -- see docstring); got {in_memory_count}/{N_ENTRIES}. "
        "If this assertion is now failing, the underlying liblcm rollback "
        "mechanism has CHANGED AGAIN -- report the new count, it is "
        "P0-severity either way."
    )
    assert surviving_count == N_ENTRIES, (
        f"MEASURED LIVE: {N_ENTRIES}/{N_ENTRIES} survivors after a genuine "
        f"close-and-reopen (same measured non-rollback, confirmed on disk); "
        f"got {surviving_count}/{N_ENTRIES}. If this assertion is now "
        "failing, the underlying liblcm rollback mechanism has CHANGED "
        "AGAIN -- report the new count, it is P0-severity either way."
    )


# ===========================================================================
# T7 -- C15 finally-guarantee, MOCK/OFFLINE (NOT live verification)
# ===========================================================================
#
# No @pytest.mark.requires_live_project on this test: it never opens a
# real LCM project. It exists solely to pin CloseProject()'s finally
# structure (spec.md C15) -- Dispose()/del self.project must run even
# when something above raises -- which a live probe cannot isolate as
# cleanly as a mock can, since the live routes into the anomaly branch
# (P-3/P-5) all measure a SUCCESSFUL usm.Save(). This test forces
# usm.Save() itself to raise, a shape none of the live probes reach.
# A mock pass here is NOT a substitute for live verification of the rest
# of T7 -- see evidence/live-t7-loud-close.md for that.

def test_c15_dispose_runs_in_finally_even_when_save_raises():
    """
    MOCK/OFFLINE test (spec.md C15). Constructs a bare FLExProject without
    OpenProject() and stubs its LCM-facing surface, then forces
    usm.Save() to raise. Asserts Dispose() is still called and
    self.project is still deleted -- the finally guarantee -- and that
    the original exception still propagates (the finally must not
    swallow it).
    """
    from unittest.mock import Mock

    from flexicon.code.FLExProject import FLExProject

    project = FLExProject()
    project.writeEnabled = True
    project._undoable = True  # Phase 2: skip the Phase-1 End/anomaly logic entirely
    fake_lcm = Mock(name="fake_lcm_cache")
    project.project = fake_lcm

    fake_usm = Mock(name="fake_undo_stack_manager")
    fake_usm.Save.side_effect = RuntimeError("boom: usm.Save() failed")
    project.ObjectRepository = Mock(return_value=fake_usm)

    with pytest.raises(RuntimeError, match="boom: usm.Save\\(\\) failed"):
        project.CloseProject()

    fake_lcm.Dispose.assert_called_once()
    assert not hasattr(project, "project"), (
        "C15: del self.project must still run in the finally block even "
        "though usm.Save() raised."
    )


# ===========================================================================
# T9b -- SaveChanges() fail-open branch, MOCK/OFFLINE (NOT live verification)
# ===========================================================================
#
# No @pytest.mark.requires_live_project on this test: it never opens a
# real LCM project. Cycle-8 QC found the fail-open `except Exception` catch
# (spec.md C21, FLExProject.py ~843-859) had NO test, live or offline,
# exercising it at all -- this fills that gap. It forces the CurrentDepth
# property to raise a RuntimeError (deliberately NOT FP_ProjectError, the
# only raise the old comment named) to pin that the catch is genuinely
# `except Exception`, not narrowed to one documented type. A mock pass
# here is not a substitute for the live gate re-run this task also
# performs -- see evidence/live-t9-failopen-coverage.md.

def test_savechanges_failopen_depth_read_raises_reaches_usm_save(caplog):
    """
    MOCK/OFFLINE test (spec.md C21, cycle-8 QC follow-up). Forces the
    `CurrentDepth` property itself to raise a non-`FP_ProjectError`
    exception, then asserts all three of:
      (a) a WARNING naming the depth-guard evaluation failure is emitted,
      (b) no `FP_TransactionError` propagates out of `SaveChanges()`, and
      (c) `usm.Save()` IS reached and called exactly once.
    (c) is the point of the test: it pins the fail-open behaviour so a
    future silent change to fail-closed cannot pass green.
    """
    import logging as _logging
    from unittest.mock import Mock, PropertyMock, patch

    from flexicon.code.FLExProject import FLExProject
    from flexicon.code.exceptions import FP_TransactionError  # noqa: F401 (documents the type that must NOT be raised)

    project = FLExProject()
    project.writeEnabled = True
    project._undoable = True
    project.project = Mock(name="fake_lcm_cache")

    fake_usm = Mock(name="fake_undo_stack_manager")
    project.ObjectRepository = Mock(return_value=fake_usm)

    with patch.object(
        FLExProject,
        "CurrentDepth",
        new_callable=PropertyMock,
        side_effect=RuntimeError(
            "boom: depth read failed for a reason unrelated to "
            "FP_ProjectError's missing-self.project check"
        ),
    ):
        with caplog.at_level(_logging.WARNING, logger="flexicon.code.FLExProject"):
            project.SaveChanges()  # must NOT raise FP_TransactionError (or anything else)

    warning_records = [
        r for r in caplog.records
        if r.levelno == _logging.WARNING
        and "could not evaluate the issue #243 depth" in r.message
    ]
    assert warning_records, (
        "Expected a WARNING naming the depth-guard evaluation failure; "
        f"got records: {[r.message for r in caplog.records]}"
    )
    assert any("RuntimeError" in r.message for r in warning_records), (
        "The WARNING should name the actual exception type (RuntimeError "
        "here) to prove the catch is `except Exception`, not narrowed to "
        "FP_ProjectError."
    )

    fake_usm.Save.assert_called_once()
