# Live verification evidence -- issue #250 Defects 1, 2 and 3

**Task:** Resolve remaining scope of issue #250 (Defect 4 already fixed/shipped).
**Project:** `target_sandbox` ONLY (fresh tempdir copy of the Target `.fwbackup`).
Never the in-place Target, never Sena 3.
**Live test file:** `tests/operations/test_issue250_defects123_ws_activation_live.py`
**Offline test file:** `tests/operations/test_issue250_defects123_ws_activation.py`
**Fix locations:**
- `flexicon/code/System/WritingSystemOperations.py` -- `Exists()` narrowed to
  active-only, new `ExistsInStore()`, `Create()` reuse-and-activate branch, new
  `Ensure()`.
- `flexicon/code/BaseOperations.py` -- `_apply_props_loop`'s multistring
  resolution drop site, now logging a warning before the unchanged `continue`.

---

## Environment

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"   # (bash: export FLEXLIBS_REQUIRE_LIVE=1)
python -m pytest tests/operations/test_issue250_defects123_ws_activation_live.py \
    -m requires_live_project -q
```

`tests/live_status.json` -> `"run_mode": "live"` on every run below (confirmed
by re-reading the file after each invocation, not assumed).

---

## Constructing "store-present-but-inactive" state live

The task instructions flagged this as possibly needing FieldWorks' UI. It does
not: exploratory live run against `target_sandbox` (script inlined below,
executed via a throwaway pytest test and discarded) confirmed the following
sequence reproduces the exact divergence the issue describes, with no UI
involved:

```python
ws = project.WritingSystems.Create(tag, name, is_vernacular=False)
# ws.Id now in CurAnalysisWss, in AnalysisWritingSystems (full list), and in
# ServiceLocator.WritingSystems.AllWritingSystems (the store).

current_list = project.lp.CurrentAnalysisWritingSystems
current_list.Remove(ws)
# Removes ONLY from the current/active list.
```

Exploratory transcript (target_sandbox, unfixed code, 2026-09-10):

```
CurVernWss: etu
CurAnalysisWss: en
AllWritingSystems: ['en', 'etu']
VernacularWritingSystems (full): ['etu']
AnalysisWritingSystems (full): ['en']
After create - CurAnalysisWss: en qaa-x-zzztest
After create - AnalysisWritingSystems (full): ['en', 'qaa-x-zzztest']
After create - AllWritingSystems: ['en', 'qaa-x-zzztest', 'etu']
After deactivate (current only) - CurAnalysisWss: en
After deactivate - AnalysisWritingSystems (full): ['en', 'qaa-x-zzztest']
After deactivate - AllWritingSystems: ['en', 'qaa-x-zzztest', 'etu']
Exists(tag) [old semantics via _GetWSByTag]: True
tag in active tags: False
```

This confirms: after removing only from the current list, the tag (a) remains
in `AllWritingSystems` (the store WritingSystemOperations._GetWSByTag scans),
(b) remains in the full per-project list, and (c) is absent from
`CurAnalysisWss`. This is exactly "a writing system that was configured and
later deactivated" -- the issue's own description of the common trigger
state -- reproduced without any FieldWorks UI interaction. The helper
`_make_store_present_inactive_ws()` in the live test file encodes this
sequence and is reused by every Defect 1/2/3 live test.

The sandbox's only two pre-existing active writing systems are `en` (analysis)
and `etu` (vernacular), matching the D4 evidence file's note; all writing
systems this file constructs are new `qaa-x-d250*` private-use tags, so no
existing project state is depended on beyond that.

---

## Per-defect live verdicts

### Defect 1 -- `Exists()` active-only vs `ExistsInStore()`

**Test:** `TestExistsAndExistsInStoreLive::test_store_present_inactive_tag_diverges_exists_vs_existsinstore`

Pre-state (re-read from the LCM after construction):
- `qaa-x-d250a` present in `AllWritingSystems`: confirmed True.
- `qaa-x-d250a` in `CurAnalysisWss.split()`: confirmed False.

Post-fix result: `Exists('qaa-x-d250a')` == `False`; `ExistsInStore('qaa-x-d250a')`
== `True`.

Pre-fix result (fix reverted via `git apply -R` on the two source files, same
test file, same command): `Exists('qaa-x-d250a')` == `True` (whole-store scan
finds it) -- **the drop demonstrated**, not assumed. `ExistsInStore` did not
exist pre-fix (`AttributeError`), consistent with it being new API surface.

**VERDICT: PASS (live, `run_mode: live`), red-then-green confirmed.**

### Defect 2 -- `Create()` activates a store-present-but-inactive tag

**Test:** `TestCreateActivationLive::test_create_activates_without_raising_or_duplicating`

Pre-state: `qaa-x-d250b` present in store, absent from `CurAnalysisWss`;
`pre_count` = store writing-system count before the second `Create()` call.

Action: `project.WritingSystems.Create('qaa-x-d250b', 'D250b Renamed',
is_vernacular=False)`.

Post-state, re-read from the LCM after the call (not the value passed in):
- `post_count == pre_count` -- confirmed no duplicate `WritingSystemDefinition`
  was created.
- `ws.Handle == original_ws.Handle` -- confirmed the SAME writing system was
  returned/reused, not a new object.
- `'qaa-x-d250b' in project.lp.CurAnalysisWss.split()` -- confirmed True,
  re-read after the call: the tag is now active.

Pre-fix result (same test, fix reverted): `Create()` raised
`FP_ParameterError: Writing system 'qaa-x-d250b' already exists` -- **the
original Defect 2 failure mode reproduced live**, not assumed from reading the
code.

**VERDICT: PASS (live, `run_mode: live`), red-then-green confirmed.**

### Defect 2 (API gap) -- `Ensure()`

**Tests:** `TestEnsureLive::test_ensure_activates_store_present_tag_and_is_idempotent`,
`TestEnsureLive::test_ensure_creates_genuinely_new_tag`

Store-present-but-inactive case (`qaa-x-d250c`, vernacular):
- First `Ensure()` call: `created == False`; `'qaa-x-d250c' in
  project.lp.CurVernWss.split()` re-read as True; store count unchanged
  (`pre_count` == post-call count).
- Second `Ensure()` call (idempotency): `created == False`; returned handle
  identical to the first call's and to the originally-created object's handle;
  store count still unchanged.

Genuinely-new case (`qaa-x-d250d`, analysis): `created == True`; store count
increased by exactly 1 (re-read); `'qaa-x-d250d' in
project.lp.CurAnalysisWss.split()` confirmed True.

Pre-fix result (fix reverted): both tests failed with
`AttributeError: 'WritingSystemOperations' object has no attribute 'Ensure'`
-- confirms the method is genuinely new, not a rename of existing behaviour.

**VERDICT: PASS (live, `run_mode: live`), red-then-green confirmed.**

### Defect 3 -- silent-drop diagnostics, and composition with Defect 2's fix

**Test:** `TestApplyPropsLoopDefect3DiagnosticsLive::test_drop_is_logged_then_resolves_after_ensure`

Setup: a real `TEST_D250e` POS created via `POSOperations.Create`; a
store-present-but-inactive analysis tag `qaa-x-d250e`.

Step 1 -- drop, captured via `caplog` at WARNING against logger `"flexicon"`:
`pos_ops.ApplySyncableProperties(pos, {"Name": {"qaa-x-d250e":
"ShouldBeDropped"}}, ws_map=None)`. Result: exactly one WARNING record whose
message names `qaa-x-d250e`; `'qaa-x-d250e' not in
project.lp.CurAnalysisWss.split()` confirmed unchanged (the drop itself is
unaffected by this fix, only its observability).

Step 2 -- activate: `project.WritingSystems.Ensure('qaa-x-d250e', 'D250e',
is_vernacular=False)` -> `created == False`.

Step 3 -- re-apply the SAME call shape with the SAME tag:
`pos_ops.ApplySyncableProperties(pos, {"Name": {"qaa-x-d250e":
"ShouldBeSaved"}}, ws_map=None)`. No WARNING naming the tag this time.

Step 4 -- re-read from the LCM: `pos` re-fetched via `IPartOfSpeech(
project.Object(hvo))` (a fresh object, not the stale pre-write reference),
`Name.get_String(handle).Text` where `handle` comes from a freshly rebuilt
`{w.Id: w.Handle for w in project.WritingSystems.GetAll()}` (i.e. the ACTIVE
set, post-activation). Result: `"ShouldBeSaved"` -- confirmed the same call
path that dropped now saves, once the target writing system is genuinely
active, and confirms the earlier drop was specific to WS inactivity and not
some other fault masking a false pass.

Pre-fix result (fix reverted, same test): 0 WARNING records for the drop step
(`AssertionError: expected a WARNING ... got []`) -- **the silent drop
demonstrated live**, not assumed.

**VERDICT: PASS (live, `run_mode: live`), red-then-green confirmed.**

---

## C-D4-6-style invariant (writing-system count / active sets never widened
unexpectedly)

Every test above re-reads `ServiceLocator.WritingSystems.AllWritingSystems`
count and/or `CurVernWss`/`CurAnalysisWss` before and after the action under
test and asserts the count changes by exactly the expected amount (0 for
reuse/activation, +1 only for a genuinely new tag in the `Ensure()`
"genuinely new" test). No test observed an unexpected widening.

---

## Full run transcript (fixed code, final state)

```
$ export FLEXLIBS_REQUIRE_LIVE=1
$ python -m pytest tests/operations/test_issue250_defects123_ws_activation_live.py -m requires_live_project -q
.....                                                                    [100%]
5 passed in 7.53s
```

`tests/live_status.json` `"run_mode"` == `"live"` immediately after this run.

## Red-then-green summary (fix reverted via `git apply -R` on
`flexicon/code/System/WritingSystemOperations.py` and
`flexicon/code/BaseOperations.py`, same live test file, same command)

```
5 failed in 8.24s
  TestExistsAndExistsInStoreLive::test_store_present_inactive_tag_diverges_exists_vs_existsinstore
  TestCreateActivationLive::test_create_activates_without_raising_or_duplicating
  TestEnsureLive::test_ensure_activates_store_present_tag_and_is_idempotent
  TestEnsureLive::test_ensure_creates_genuinely_new_tag
  TestApplyPropsLoopDefect3DiagnosticsLive::test_drop_is_logged_then_resolves_after_ensure
```

Fix re-applied (`git apply`) immediately after this run; green state confirmed
again (see transcript above) before moving on.

---

## Offline suite regression check

`python -m pytest tests/ -q -m "not requires_live_project"` before vs. after
this change (both runs against the identical concurrent-agent working tree,
isolated by stashing only the two files this task owns):

- With the two owned files stashed (i.e. pre-fix, but with every OTHER
  concurrent agent's uncommitted work present): 4 failed, 84 passed (subset
  run against the two pre-existing-failing files) / 4 failed total in the
  full offline suite at the time of the check.
- With the fix applied: identical 4 pre-existing failures
  (`test_collection_cast_pattern.py` x2, `test_docstring_example_ratchet.py`
  x2), confirmed by `git stash push` on only
  `flexicon/code/BaseOperations.py` and
  `flexicon/code/System/WritingSystemOperations.py` (not a full-tree stash,
  to avoid disturbing concurrent agents' in-progress uncommitted work) --
  identical failure set with and without this task's diff. **Zero new
  offline regressions.**
- Full offline suite, fix applied, this task's new test files included:
  `2 failed, 1675 passed, 625 deselected` (the 2 pre-existing
  `test_docstring_example_ratchet.py` failures; confirmed present on the
  stashed/clean tree too, unrelated to writing systems).
- `tests/operations/test_issue250_defect4_ws_resolution.py` (owned by the
  concurrent #266 agent, not edited by this task): 21 passed at time of
  final check (the resolution-site ratchet, which showed a transient failure
  earlier in this session due to the #266 agent's own in-progress work, was
  green again by the time of the final full-suite run -- not caused by, and
  not fixed by, this task).
