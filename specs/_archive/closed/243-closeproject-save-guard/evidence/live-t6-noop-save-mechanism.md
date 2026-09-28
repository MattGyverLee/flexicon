# Evidence -- T6 no-op-save mechanism probe (issue #243, Checkpoint 2c)

Date: 2026-09-07 (spurt 5, cycle 5)
Fixture: `target_sandbox_path` ONLY. The real Target project was never
opened; no `scripts/restore_*.py` was run.
No file under `flexicon/` was touched -- see the `git diff --stat -- flexicon/`
output below (empty). Only `tests/operations/test_issue243_closeproject_probe.py`
was extended, plus this evidence file and the cycle-5 report.

## Commands, in order, with `--collect-only` derivations

The probe file's live-test count grows again here, from 6 (frozen at CP-B) to
**9** (P-7, P-8, P-9 added):

```
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py --collect-only -q -m requires_live_project
tests/operations/test_issue243_closeproject_probe.py::test_p1_mode_matrix
tests/operations/test_issue243_closeproject_probe.py::test_p2_depth_table
tests/operations/test_issue243_closeproject_probe.py::test_p2_public_surface_matches_depth_table
tests/operations/test_issue243_closeproject_probe.py::test_p3_p6_reproduction_and_symptom
tests/operations/test_issue243_closeproject_probe.py::test_p4_control_run_normal_close
tests/operations/test_issue243_closeproject_probe.py::test_p5_save_before_forced_end
tests/operations/test_issue243_closeproject_probe.py::test_p7_data_survives_failed_savechanges_in_memory
tests/operations/test_issue243_closeproject_probe.py::test_p8_fresh_entry_after_failed_savechanges
tests/operations/test_issue243_closeproject_probe.py::test_p9_iundostackmanager_detector

9 tests collected in 0.17s
```

```
$ python -m pytest tests/operations/test_undoable_mode_live.py --collect-only -q -m requires_live_project
...
33 tests collected in 0.96s
```

```
$ python -m pytest tests/operations/test_target_live_smoke.py --collect-only -q -m requires_live_project
...
3 tests collected in 0.13s
```

All three counts match the boilerplate table plus the +3 growth called for
by `tasks.md` T6 (6 -> 9, undoable-mode 33 unchanged, target-smoke 3
unchanged).

## Live runs (`FLEXLIBS_REQUIRE_LIVE=1`)

```
$ export FLEXLIBS_REQUIRE_LIVE=1
$ python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s
9 passed, 1 warning in 8.82s
```

```
$ python -m pytest tests/operations/test_undoable_mode_live.py -m requires_live_project -q
33 passed, 1 warning in 13.54s
```

```
$ python -m pytest tests/operations/test_target_live_smoke.py -m requires_live_project -q
3 passed, 4 warnings in 3.82s
```

`tests/live_status.json` after this run:

```json
"run_mode": "live",
"run_timestamp": "2026-09-07T14:33:48Z",
```

`run_mode` is `"live"` -- this run measured real LCM behaviour, not mocks.
(`test_transaction_rollback.py` is the OFFLINE-only file per the frozen
boilerplate table; not re-run live here since T6 does not touch it.)

## Offline baseline

```
$ python -m pytest tests -m "not requires_live_project" -q
1290 passed, 473 deselected, 17 warnings in 10.31s
```

Unchanged at **1290 passed** (the frozen pre-T1 baseline). Deselected count
rose from 470 (T4's evidence) to 473 -- exactly the +3 new
`requires_live_project` tests added by this task, not a regression.

## Scope fence check

```
$ git diff --stat -- flexicon/
(empty)
$ git diff --stat -- tests/operations/test_issue243_closeproject_probe.py
 tests/operations/test_issue243_closeproject_probe.py | 578 +++++++++++++++++++++
 1 file changed, 578 insertions(+)
```

No file under `flexicon/` was touched. `SaveChanges()` and `CloseProject()`
are observed only, via public API calls made directly by the test (the same
pattern P-2/P-3/P-5 already used to force the End mirror manually).

---

## P-7 -- is the data still there? (mechanism (ii) ceiling test)

Setup: 25 `TEST_p7_` entries created, `SaveChanges()` called at
`CurrentDepth == 1` (raises the owner's exact `Commit at wrong place.`
string, `CurrentDepth` drops 1 -> 0 as a side effect, both matching cycle 1
/ T4 exactly). Then, **without closing or reopening**, `LexEntry.GetAll()`
was re-read from the STILL-OPEN project.

Measured console output:

```
[PROBE][P7] created 25 entries with prefix 'TEST_p7_'
[PROBE][P7] CurrentDepth before SaveChanges(): 1
[PROBE][P7] CurrentDepth after SaveChanges() raised: 0
[PROBE][P7] TEST_ entries still visible in the STILL-OPEN project after SaveChanges() raised: 0 / 25
[PROBE][P7] VERDICT: mechanism (ii) CONFIRMED -- SaveChanges()'s failure path discarded the pending change set outright. THIS SETTLES #243's CEILING: no CloseProject()-side change can ever reach 25/25 for the owner's real P-5 -> P-3 sequence, because the data is already gone before CloseProject() is ever entered.
[PROBE][P7] TEST_ entries surviving a real reopen, re-read from LCM: 0 / 25
[PROBE][P7] SUMMARY: in-memory (still-open) count=0/25, post-reopen count=0/25
```

**Result: 0/25, in-memory, before `CloseProject()` was ever called.**

**Mechanism (ii) is CONFIRMED.** The pending change set was already gone
-- not merely uncommitted, but absent from `LexEntry.GetAll()` on the
still-open project -- one full step before `CloseProject()` is ever
entered. This settles #243's ceiling: **no change on the `CloseProject()`
side can ever reach 25/25 for the owner's actual P-5 -> P-3 sequence**,
because the data does not survive as far as `CloseProject()`'s own code at
all. (It does, unambiguously, still fix the independent P-3 scenario --
0/25 -> 25/25 -- where the change set is intact and only the End mirror is
forced to fail; C13 fact 1 already established that T3 is not implicated by
either result.)

## P-8 -- globally poisoned, or only the existing dirty set?

Setup: 25 `TEST_p8setup_` entries, `SaveChanges()` raises and collapses the
envelope exactly as in P-7. Then a **fresh** `BeginNonUndoableTask()` /
`EndNonUndoableTask()` pair was opened and closed manually, with exactly one
new `TEST_p8fresh_` entry created inside it, before `CloseProject()`.

Measured console output:

```
[PROBE][P8] created 25 setup entries with prefix 'TEST_p8setup_'
[PROBE][P8] CurrentDepth after SaveChanges() raised: 0
[PROBE][P8] CurrentDepth after fresh BeginNonUndoableTask(): 1
[PROBE][P8] created 1 fresh entry with prefix 'TEST_p8fresh_'
[PROBE][P8] CurrentDepth after fresh EndNonUndoableTask(): 0
[PROBE][P8] setup entries surviving (pre-existing dirty set): 0 / 25
[PROBE][P8] fresh entry surviving (post-failure envelope): 1 / 1
[PROBE][P8] VERDICT: NOT globally poisoned -- a freshly-opened envelope created AFTER the failed SaveChanges() commits fine. Mechanism (i) (session-wide UOW poisoning) is RULED OUT; (ii)/(iii) (only the pre-existing dirty set is unusable) are favoured over (i).
[PROBE][P8] SUMMARY: setup=0/25 fresh=1/1
```

**Result: setup 0/25 (reconfirms P-7/T4), fresh entry 1/1.**

**Mechanism (i) (session-wide `UnitOfWorkService`/`UndoStack` poisoning) is
RULED OUT.** A fresh envelope opened and cleanly ended AFTER the failed
`SaveChanges()` commits its one new entry without incident, in the same
process, same `usm`, same session. The service itself is not broken; only
the specific, already-dirty change set that was in flight when
`CheckReadyForCommit` failed is unrecoverable.

## P-9 -- the detector, and CP-B defect 2

### Reflection: the live `IUndoStackManager`'s actual member list

Concrete runtime type: `SIL.LCModel.Infrastructure.Impl.UnitOfWorkService`

`dir()` on the live object (verbatim):

```
['ActiveUndoStack', 'BeginReadTask', 'ConflictingChanges', 'CreateReconciler', 'CreateUndoStack', 'CurrentUndoStack', 'Dispose', 'DisposeStack', 'EndReadTask', 'Equals', 'Finalize', 'GatherChanges', 'GetHashCode', 'GetType', 'HasUnsavedChanges', 'IsDisposed', 'IsNew', 'MemberwiseClone', 'OnSave', 'Overloads', 'ReferenceEquals', 'Refresh', 'Save', 'SetCurrentStack', 'StopSaveTimer', 'ToString', 'UnsavedUnitsOfWork', '__class__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__overloads__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', 'add_OnSave', 'get_ActiveUndoStack', 'get_CurrentUndoStack', 'get_HasUnsavedChanges', 'get_IsDisposed', 'get_UnsavedUnitsOfWork', 'remove_OnSave']
```

.NET `Type.GetProperties()` (verbatim):

```
['ActiveUndoStack', 'CurrentUndoStack', 'HasUnsavedChanges', 'IsDisposed', 'UnsavedUnitsOfWork']
```

.NET `Type.GetMethods()`, accessor prefixes filtered (verbatim):

```
['BeginReadTask', 'ConflictingChanges', 'CreateReconciler', 'CreateUndoStack', 'Dispose', 'DisposeStack', 'EndReadTask', 'Equals', 'GatherChanges', 'GetHashCode', 'GetType', 'IsNew', 'Refresh', 'Save', 'SetCurrentStack', 'StopSaveTimer', 'ToString']
```

Candidate "has unsaved/pending changes" members found by keyword search
(`Unsaved`, `Pending`, `Dirty`, `HasChange`, `NeedsSave`, `IsSaved`):

```
['HasUnsavedChanges', 'UnsavedUnitsOfWork', 'get_HasUnsavedChanges', 'get_UnsavedUnitsOfWork']
```

**`HasUnsavedChanges` (boolean property) is present and readable on the
live object.** This matches `tests/contract/snapshots/liblcm_baseline.json`'s
existing `IUndoStackManager` entry.

### Measurement: no-op shape (mirrors P-5) vs. real-save shape (mirrors P-4)

No-op shape console output (verbatim):

```
[PROBE][P9] (no-op shape) created 25 entries with prefix 'TEST_p9noop_'
[PROBE][P9] (no-op shape) HasUnsavedChanges before the TRIGGER SaveChanges(): False
[PROBE][P9] (no-op shape) HasUnsavedChanges after the TRIGGER SaveChanges() raised: False
[PROBE][P9] (no-op shape) CurrentDepth before the no-op Save(): 0
[PROBE][P9] (no-op shape) HasUnsavedChanges BEFORE the no-op usm.Save(): False
[PROBE][P9] (no-op shape) second SaveChanges() call raised: None
[PROBE][P9] (no-op shape) HasUnsavedChanges AFTER the no-op usm.Save(): False
[PROBE][P9] (no-op shape) entries surviving reopen (confirms this really was a no-op save): 0 / 25
```

Real-save (control) shape console output (verbatim):

```
[PROBE][P9] (real-save shape) created 25 entries with prefix 'TEST_p9real_'
[PROBE][P9] (real-save shape) CurrentDepth before ending the real envelope: 1
[PROBE][P9] (real-save shape) HasUnsavedChanges BEFORE usm.Save(): True
[PROBE][P9] (real-save shape) HasUnsavedChanges AFTER usm.Save(): False
[PROBE][P9] (real-save shape) entries surviving reopen (confirms this really was a real save): 25 / 25
```

Summary and distinguishability verdict (verbatim):

```
[PROBE][P9] SUMMARY -- detector present: True. no-op shape: before_trigger=False after_trigger=False before_noop_save=False after_noop_save=False (reopen confirmed 0/25 persisted). real-save shape: before_real=True after_real=False (reopen confirmed 25/25 persisted).
[PROBE][P9] AFTER-ONLY comparison: no-op AFTER=False vs real AFTER=False -- INDISTINGUISHABLE.
[PROBE][P9] BEFORE-value comparison: no-op BEFORE=False vs real BEFORE=True -- DISTINGUISHABLE.
[PROBE][P9] HasUnsavedChanges read immediately AFTER usm.Save() CANNOT by itself tell a no-op save from a real one -- both read False once Save() has returned, whether or not anything was actually persisted.
[PROBE][P9] However, HasUnsavedChanges read immediately BEFORE usm.Save() DOES distinguish the two shapes here: True in the real-save shape (a successful End registered the pending edits as an unsaved-but-committed unit of work) vs False in the no-op shape (the forced End never succeeded, so the pending edits were never registered as unsaved work in the first place -- consistent with mechanism (ii)/P-7's in-memory-loss finding). This is a CANDIDATE pre-Save() detector for T7: read HasUnsavedChanges on entry to the anomalous HasOpenSessionTask()==False branch; False there means usm.Save() is about to be a no-op. Not proven mechanism-independent (P-8 ruled out mechanism (i) here, so this signal was only observed under (ii)/(iii); a future spurt would need to re-check it against a case that isolates (i) if one is ever found) -- but it is a real, measured, distinguishing signal, unlike the after-Save() read.
```

### P-9 verdict

- **After-Save() read: INDISTINGUISHABLE.** `HasUnsavedChanges` reads
  `False` immediately after `usm.Save()` in BOTH shapes -- a real save that
  actually persisted 25/25, and a no-op save that persisted 0/25. A
  post-Save() read of this property alone cannot tell them apart. This
  directly answers Q5's "genuinely open" question in the negative for the
  naive form of the detector.
- **Before-Save() read: DISTINGUISHABLE, but not proven
  mechanism-independent.** `HasUnsavedChanges` reads `True` before the real
  save (a successful `EndNonUndoableTask()` had just registered the pending
  edits) and `False` before the no-op save (the forced `EndNonUndoableTask()`
  never succeeded, so nothing was ever registered). This correlates
  precisely with P-7's finding that the change set is gone from
  `LexEntry.GetAll()` before `CloseProject()` is even entered -- both are
  symptoms of the same discarded-change-set mechanism (ii). It has NOT been
  tested against a scenario that isolates mechanism (i), because P-8 ruled
  (i) out entirely in this run; so it is a real, measured signal for the
  mechanism actually present, not a proven general-purpose "is this about
  to be a no-op" oracle for every possible cause.
- **Bearing on T7:** a pure post-Save() `HasUnsavedChanges` check is
  unusable as T7's sole detector. The Phase-1-envelope-missing heuristic
  (already computable from T1's `HasOpenSessionTask()` surface, named as
  the fallback in spec.md C14 point 3) remains necessary. The pre-Save()
  `HasUnsavedChanges` read is a plausible SUPPLEMENT once inside that
  anomalous branch (it would let T7's error message state affirmatively
  "and there is nothing pending to save" vs. "there may or may not be"),
  but it is not a replacement for the envelope-missing check, and T7 should
  not be built as though it independently proves anything beyond what was
  measured here.

## CP-B defect 2 -- `close_exc_msg` assertion added, `[PROBE][P5]` lines quoted

`test_p5_save_before_forced_end` now asserts `close_exc_msg is None`
(mirroring `test_p3_p6_reproduction_and_symptom`'s existing assertion),
closing the gap C13 fact 3 flagged. Verbatim `[PROBE][P5]` console lines
from this run (`-s`, full transcript for the test):

```
[PROBE][P5] created 25 entries with prefix 'TEST_p5_'
[PROBE][P5] CurrentDepth before SaveChanges(): 1
[PROBE] P5 SaveChanges() while envelope still open: RAISED InvalidOperationException: Commit at wrong place.
   at SIL.LCModel.Infrastructure.Impl.UndoStack.CheckReadyForCommit(String message)
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.SaveInternal()
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.Save()
[PROBE] P5 CurrentDepth after SaveChanges(): OK -> 0
[PROBE][P5] CurrentDepth after SaveChanges() attempt: 0
[PROBE] P5 manual EndNonUndoableTask (post-SaveChanges): RAISED InvalidOperationException: Cannot end task that has not been started.
   at SIL.LCModel.Infrastructure.Impl.UndoStack.EndUndoTaskCommon(Boolean updateDateModified)
[PROBE] P5 CloseProject (expected to succeed under T3 guard): OK -> None
[PROBE][P5] TEST_ entries surviving, re-read from LCM: 0 / 25
[PROBE] P5 reopen CloseProject: OK -> None
[PROBE][P5] SaveChanges() raise UNCHANGED by T3: InvalidOperationException: Commit at wrong place.
   at SIL.LCModel.Infrastructure.Impl.UndoStack.CheckReadyForCommit(String message)
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.SaveInternal()
   at SIL.LCModel.Infrastructure.Impl.UnitOfWorkService.Save()
[PROBE][P5] GO/NO-GO VERDICT (T3 guard, measured not assumed): 0/25 survived -- NEW FINDING, not a partial fix: a UnitOfWorkService whose commit check already failed (via SaveChanges()) is unrecoverable even once the guard lets usm.Save() run. Recorded as a dated note under spec.md Q2; would require a companion guard on SaveChanges() itself (out of scope for T3/T4, routed to QUEUE.md 'Awaiting user approval').
```

`[PROBE] P5 CloseProject (expected to succeed under T3 guard): OK -> None`
is the load-bearing line: `_safe()`'s own convention prints `OK -> <result>`
only on success, and `CloseProject()` returns `None`, so this line IS the
"`CloseProject()` did not raise" claim C13 fact 3 depends on, now backed by
`assert close_exc_msg is None` in the test itself rather than left as prose.

---

## C13 mechanism verdict

**Mechanism (ii) is CONFIRMED. Mechanism (i) is RULED OUT.** Mechanism
(iii) (envelope-collapse un-registers the dirty objects, leaving `Save()`
to correctly flush an empty set) is not separately distinguishable from
(ii) by anything measured here -- P-7 shows the objects are gone from
`LexEntry.GetAll()` itself, which is consistent with either "the change set
was discarded" (ii) or "the objects were unregistered from any commitable
unit of work" (iii) producing the same externally-visible symptom; both
describe the SAME loss point (inside/immediately after the failed
`SaveChanges()`, before `CloseProject()` is ever entered), so the
scope-relevant conclusion is identical either way and no further
measurement in this campaign distinguishes them. If a future investigation
needs to split (ii) from (iii) specifically, it would need instrumentation
inside liblcm itself (outside this project's reach), not a black-box
`flexicon` probe.

- **(i) session-wide UOW/UndoStack poisoning: RULED OUT** by P-8 -- a fresh
  envelope opened and closed after the failure commits its own new entry
  (1/1) in the same process.
- **(ii) `SaveChanges()`'s failure path discarded the pending change set
  outright: CONFIRMED** by P-7 -- the 25 entries are already absent from
  `LexEntry.GetAll()` on the STILL-OPEN project immediately after
  `SaveChanges()` raises, one full step before `CloseProject()` is ever
  entered.
- **This settles #243's ceiling for the owner's real P-5 -> P-3 sequence:
  no `CloseProject()`-side change (T3's guard, or any future guard in that
  method) can ever recover the owner's data**, because it does not survive
  as far as `CloseProject()`'s own code path. The only place a fix for the
  owner's actual incident could live is `SaveChanges()` itself (the queued,
  user-ruling-pending fourth ask) -- consistent with, and now measured
  proof for, what C13's closing paragraph already anticipated ("all three
  mechanisms imply the SAME shape for the queued fourth ask").
- T3's P-3 fix (0/25 -> 25/25 for the independent forced-double-End
  scenario, where the change set is intact) is unaffected by any of this
  and stands as shipped (C13 fact 1, re-confirmed, not re-litigated).

No further measurement is needed to separate (i) from (ii)/(iii) for
scoping purposes -- P-8 alone rules out (i), and P-7 alone confirms the
practical consequence of (ii)/(iii). Separating (ii) from (iii)
specifically is NOT decision-relevant to #243 (both name the identical
scope conclusion above) and is left unresolved by design, per this
evidence.

## PASS/FAIL

**PASS.** All required live suites green with `run_mode: live` (probe 9/9,
undoable-mode 33/33, target-smoke 3/3); full offline suite unchanged at
1290 passed (deselected count grew by exactly +3, matching the new live
tests). `git diff --stat -- flexicon/` is empty -- no behaviour change to
any `flexicon/` file. CP-B defect 2 closed (`close_exc_msg` now asserted in
`test_p5_save_before_forced_end`, `[PROBE][P5]` lines quoted verbatim
above). P-7/P-8/P-9 all measured, not assumed, with the mechanism verdict
(ii CONFIRMED, i RULED OUT) and the detector verdict (post-Save() read
unusable alone; pre-Save() read is a real but not-proven-general signal)
both recorded above.
