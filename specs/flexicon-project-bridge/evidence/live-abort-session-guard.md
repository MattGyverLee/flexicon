# Live LCM evidence -- attached-view guard on `AbortSession()`

Feature: flexicon-project-bridge (`FLExProject.FromOpenProject()`).
The spec body for this feature lives in the FlexToolsMCP repo; this file is
the live-verification record required by `CLAUDE.md` for the write-path
change made in this repo.

Change under test: `FLExProject.AbortSession()` now refuses on a project
attached with `FromOpenProject()`, before any action-handler access.

Date: 2026-09-09
Project used: **Target**, via the `target_sandbox` fixture (a write-enabled
tempdir copy restored from the Target `.fwbackup`). A sandbox rather than the
real Target because the defect under test is an unwanted `Rollback(0)` of a
whole session -- a regression here destroys data by definition.

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_attached_view_abort_live.py -m requires_live_project -q
```

Result: **6 passed in 5.33s** (re-run for the ledger below: 6 passed in 5.12s)

### The live ledger, transcribed

`tests/live_status.json` is **gitignored** (`.gitignore:103`), so it cannot
itself serve as durable evidence -- any later run clobbers it. It did get
clobbered once: a throwaway probe (`tests/operations/test_zz_probe_tmp.py`,
since deleted) overwrote the original ledger for this run, leaving the claim
below unbacked until it was re-run. The ledger is therefore transcribed here,
from a re-run of the exact command above:

```json
"run_mode": "live",
"run_timestamp": "2026-09-10T02:37:33Z",
"uncategorized_live_tests": []
```

All six tests are named in `by_test`, each `"status": "pass"`, each attributed
to `operations_class: FLExProject`:

| Test | Phase |
|---|---|
| `TestFixtureReachesLiveLCM::test_view_borrows_the_live_cache_and_is_attached` | read |
| `TestRefusalOnALiveAttachedView::test_refuses_with_the_attached_view_wording` | modify |
| `TestHostDataSurvivesTheRefusal::test_host_edit_made_before_the_module_ran_survives` | modify |
| `TestHostEnvelopeSurvivesTheRefusal::test_current_depth_is_unchanged` | modify |
| `TestHostEnvelopeSurvivesTheRefusal::test_host_can_still_write_after_the_refusal` | modify |
| `TestHostEnvelopeSurvivesTheRefusal::test_the_host_itself_can_still_abort` | modify |

A `"mock"` value in `run_mode` would mean this run proved nothing. It says
`live`, and `FLEXLIBS_REQUIRE_LIVE=1` was set, which converts a mock fallback
into a hard failure rather than a green pass.

## Proof the fixture reached a real LCM

```
cache type          : LcmCache
action handler type : IActionHandler
```

Not doubles: the offline doubles in `tests/test_from_open_project.py` model
liblcm's `UndoStack` from source but never execute it.

## Pre-state / post-state, read back from the LCM

Scenario is the one in the defect report: the host makes edit A before
invoking a module; the module attaches a view, makes edit B, then calls
`AbortSession()` after an error.

Every "present" line below is a fresh `POS.Find()` re-query through the
Operations layer after the call -- not the return value of the write.

| Observation | Pre | Post |
|---|---|---|
| host edit A (`TEST_host_edit_A`) present | True | **True** |
| module edit B (`TEST_module_edit_B`) present | True | True |
| `ActionHandlerAccessor.CurrentDepth` | 1 | **1** |

Call result:

```
view.AbortSession() -> raised FP_RuntimeError
message: AbortSession() is not available on a project attached with
FromOpenProject(). The open unit of work belongs to the host (FLExTools, or
FieldWorks itself), which opened it over this cache before your module was
called; rolling it back here would discard the host's own unsaved edits as
well as yours, and would leave the host holding an envelope it did not open.
A module cannot discard its writes on an attached view -- let the exception
propagate out of Main() and report it, and leave the keep-or-discard
decision to the host and its user.
```

Follow-on checks, same live session:

```
host write after refusal succeeded: True
owner AbortSession() still works  : True
after owner abort, A present      : False
after owner abort, CurrentDepth   : 1
```

The host write succeeding proves the envelope was neither ended nor
replaced -- liblcm refuses data changes outside an open unit of work. The
last two lines prove the guard did not neuter the owned path on the very
same cache: the owner's own abort still discards (A gone) and still reopens
the envelope (depth back to 1).

## Negative control (offline, same day)

With the guard removed, the same scenario against the offline doubles:

```
PRE :  depth=1 rollback_calls=[] begin_calls=0
RESULT: True
POST:  depth=1 rollback_calls=[0] begin_calls=1
```

i.e. unguarded, the view called `Rollback(0)` on the host's action handler
and then `BeginNonUndoableTask()` to install a replacement envelope, and
reported success. Six of the eight new offline tests fail with the guard
removed; the two that still pass pin refusal prose, not behaviour.

## Verdict

**PASS: live-verified.** The refusal fires against a real `IActionHandler`,
the host's uncommitted edit and its `CurrentDepth` are both untouched, the
host remains writable, and the owned-project rollback path is unchanged.
