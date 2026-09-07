# SPEC -- 243-closeproject-save-guard

**Repo:** flexicon, branch `main`
**Issue:** #243 (`CloseProject()` unguarded `EndNonUndoableTask()` risks total
session loss)
**Status:** CONTRACT FROZEN. Cycle-1 live probe complete. **T1 LANDED and
live-verified (spurt 2, cycle 2, 2026-09-07)** -- `flexicon/code/FLExProject.py`
now exposes the P1 depth-read surface (`_ReadActionHandlerDepth()`,
`CurrentDepth` property, `HasOpenSessionTask()`); the diff is purely additive
(120 insertions, 0 deletions, one file), so `CloseProject()` (T3) and
`SaveChanges()` are provably untouched. T2 is deliberately deferred to its own
gated sub-checkpoint (CP-A2) and CP-A is therefore only half done.
Q3 is now CLOSED (see Q3 below); Q2 and Q4 remain open.
Q1 RESOLVED 2026-09-07 by `/lex-lead` (see C9/C10) -- the owner's incident is
a P-5 -> P-3 chain and the frozen C6 guard covers it, so implementation is
unblocked and needs no owner input.
**Cycle-1 inputs (read these before implementing):**
- `specs/243-closeproject-save-guard/evidence/live-cycle1-probe.md` (live,
  `run_mode: live`, 5/5 passing, Target sandbox only, real Target untouched)
- `specs/243-closeproject-save-guard/reviews/cycle1-programmer.md`
- `specs/243-closeproject-save-guard/reviews/cycle1-domain.md`
- `tests/operations/test_issue243_closeproject_probe.py` (the probe harness --
  EXTEND, do not duplicate; see `tasks.md`)

---

## 1. Problem statement

`FLExProject.CloseProject()` (`flexicon/code/FLExProject.py:318-338`), under
`writeEnabled=True, undoable=False`, unconditionally calls
`self.project.MainCacheAccessor.EndNonUndoableTask()` (line 326) -- the
bookkeeping mirror for the session-long `BeginNonUndoableTask()` envelope
opened at `OpenProject()` -- before `usm.Save()` (line 332), with no guard
between them. If the End mirror raises for any reason, `usm.Save()` never
runs and the entire session's uncommitted work is lost with no data written
to disk.

**Owner-confirmed impact (as filed):** a bulk-import run reported success;
an immediate in-process inventory saw all 11,987 newly created objects;
reopening the project later showed none of them; `Target.fwdata` had been
replaced by what looked like the crash-recovery copy, its size becoming
exactly the old `Target.bak`'s size. The only symptom logged was a single
`[WARN] Commit at wrong place.` line.

**What the live probe reproduced, and what it did not** (full detail in
section 2):

| Owner's report | Probe result |
|---|---|
| Total loss of all created objects on a failed close | REPRODUCED -- P-3: 25 created, 0 survivors after a forced End-before-Save failure |
| Loss is all-or-nothing (never partial) | REPRODUCED -- P-3 (0/25) and P-4 control (25/25) bracket the result cleanly; P-5's forced failure also lands at 0/25, never partial |
| `.fwdata` "replaced by the crash-recovery copy," size changed | NOT REPRODUCED, and RULED OUT OF SCOPE -- see **C10**. On the sandbox `.fwdata` is byte-for-byte unchanged (delta 0) with no `.bak`/recovery sibling. That is the CORRECT consequence of `usm.Save()` never running: nothing was written, so nothing on disk could change. `CloseProject()` has no path that renames/rotates/replaces `.fwdata`, so no in-scope change can cause or prevent a file swap; the owner's swap is attributed to FieldWorks-side recovery and left unexplained by design. P2 must not claim this fix prevents it. |
| Literal `[WARN] Commit at wrong place.` line | REPRODUCED, and now RECONCILED -- see **C9**. The string never appears in the P-3 (double-End) sequence, which raises `Cannot end task that has not been started.` instead; it reproduces only in P-5 (`Save()` at `CurrentDepth > 0`). These are not rival explanations: P-5 is the TRIGGER (it raises the owner's exact string AND collapses the envelope, depth 1 -> 0) and P-3 is the LOSS MECHANISM (the collapsed envelope makes line 326 raise, skipping line 332). One chained sequence, both halves measured live in cycle 1. |

The originally-filed root cause for #243 (rollback destroying the
non-undoable session envelope) is a separate, already-withdrawn issue --
see section 4, "Withdrawn and out of scope."

---

## 2. Observed current behaviour (live)

Source: `specs/243-closeproject-save-guard/evidence/live-cycle1-probe.md`
(`run_mode: live`, 5/5 tests passing, `target_sandbox_path` fixture only, the
real Target project was never opened).

### P-1 -- mode matrix (is line 326 even reachable?)

| Mode | writeEnabled | `_undoable` | line 326 reached |
|---|---|---|---|
| (a) default (4.4.0), `undoable=True` | True | True | False |
| (b) `undoable=False` | True | False | True |
| (c) read-only | False | False | False |

Line 326 is reachable only under an explicit `undoable=False` opt-in.
The 4.4.0 default never reaches it.

### P-2 -- `CurrentDepth` table

| Moment | `CurrentDepth` |
|---|---|
| After `OpenProject(undoable=False)` | 1 |
| After `OpenProject(undoable=True)` | 0 |
| Inside `Transaction()` block, `undoable=False` | 1 (unchanged) |
| Inside `Transaction()` block, `undoable=True` | 0 (unchanged) |
| Inside `UndoableOperation()` block, `undoable=True` | 1 |
| After `AbortSession()` returns `True`, `undoable=False` | 1 |
| Immediately after a manual `EndNonUndoableTask()`, `undoable=False` | 0 |
| Reading `CurrentDepth` on a read-only project | 0 (no exception) |

Normal operation at the point `CloseProject()` reaches line 326 is always
depth 1; depth 0 unambiguously means "already ended." This is the exact
input a P1 depth-based guard needs (see section 3, C6).

### P-3 / P-4 / P-5 -- object survival counts

| Probe | Setup | Forced condition | Reopen count |
|---|---|---|---|
| P-3 | 25 entries | manual `EndNonUndoableTask()` before `CloseProject()` | 0/25 |
| P-4 (control) | 25 entries | none | 25/25 |
| P-5 | 25 entries | `SaveChanges()` called at `CurrentDepth=1` (envelope still open), then forced End | 0/25 |

P-5 is the fix-shape go/no-go: `usm.Save()` (via `SaveChanges()`) itself
raises `InvalidOperationException: Commit at wrong place.` when called
while `CurrentDepth > 0`, and that failure's own path drops `CurrentDepth`
from 1 to 0 as a side effect, before propagating.

---

## 3. Scope: the three surviving asks

Per `specs/tier1-silent-data-loss/QUEUE.md` section "1.
`243-closeproject-save-guard`," three items survive the owner's own
self-correction of the issue thread:

- **P0 -- the `CloseProject()` End-guard.** NOT a reorder of `Save()` ahead
  of `EndNonUndoableTask()` -- P-5 proves that shape trades one guaranteed
  raise for another with no save occurring either way (section 2). The fix
  guards the existing line-326 `End` call so a raise there cannot skip
  line 332's `usm.Save()`. End-then-Save stays the correct order.
- **P1 -- expose the LCM task-depth read.** `HasOpenSessionTask()` /
  `CurrentDepth`, mirroring the internal read three call sites already do
  (`transaction.py:172`, `undoable_operation.py:102`,
  `System/CustomFieldOperations.py:306`). This is a prerequisite of P0's
  final shape, not a follow-on -- see C6.
- **P2 -- a prominent release-note / CHANGELOG entry** for the 4.4.0
  `OpenProject(undoable=...)` default flip, cross-referencing this fix.


---

## 4. Withdrawn and out of scope -- do not re-litigate

The issue thread contains a self-correction by the repo owner. The
originally-filed root cause -- "rollback destroys the non-undoable session
envelope" -- was EXPLICITLY WITHDRAWN by the repo owner. The real trigger
for the owner's incident was the 4.4.0 `OpenProject(undoable=...)` default
flip from `False` to `True` (`CHANGELOG.md` `[4.4.0]`), which changed
callers' effective mode out from under them; that has already been fixed
consumer-side by the affected caller passing `undoable=False` explicitly.

**No change to the `undoable` default is in scope for this feature.** Do not
reopen the 4.4.0 default flip, do not propose reverting it, and do not treat
`AbortSession()`/rollback semantics as part of this feature's fix surface --
those are `specs/write-path-transactions` territory and are already shipped
and closed. This feature is scoped exclusively to the three asks in section
3. This section exists so a future spurt does not rediscover the withdrawn
root cause and re-litigate it as if it were live.

---

## 5. Acceptance criteria

1. **P0:** With a live sandbox project opened `undoable=False`, forcing the
   line-326 `EndNonUndoableTask()` mirror to have nothing to end (as in P-3)
   no longer causes total session loss -- `usm.Save()` still runs and a
   reopen shows all created objects survive. Evidence:
   `evidence/live-<task>.md` re-running the P-3 scenario against the fixed
   code, `run_mode: live`, object count re-read from the LCM after reopen.
2. **P0 regression coverage:** P-3 and P-5 (already-passing probes against
   the unfixed code) are extended in place to assert the fixed post-guard
   behaviour, and both stay green. Evidence: pytest output showing both
   tests passing against the patched `FLExProject.py`.
3. **P1:** `HasOpenSessionTask()` and `CurrentDepth` are readable from a live
   `FLExProject` and match the P-2 table's live values in every mode,
   including the closed/never-opened raise and the read-only no-raise case.
   Evidence: `evidence/live-<task>.md` re-reading each value live and
   comparing to the frozen P-2 table.
4. **P0 depends on P1:** the P0 guard's implementation calls the P1 surface
   (`HasOpenSessionTask()` or `CurrentDepth > 0`) to decide whether
   `EndNonUndoableTask()` should be attempted at all, not merely to wrap it
   in a bare `try/except`. Verifiable by code review against C6 plus the
   task-ordering in `tasks.md` (P1 tasks precede the P0 task).
5. **P2:** `CHANGELOG.md` carries a new entry (owned by `/lex-doc`, see
   `tasks.md`) cross-referencing the `[4.4.0]` `undoable` default-flip entry
   and this fix, prominent enough that a reader of the `undoable=False`
   docstring/example is pointed at it. Docs-only; no live evidence required
   (see task's exemption note).

---

## 6. Contract decisions frozen now

### C1 -- Fix shape for P0 is a GUARD, not a reorder

Per the P-5 verdict (section 2), reordering `usm.Save()` ahead of
`EndNonUndoableTask()` is REJECTED as a fix shape: `Save()` itself raises
`InvalidOperationException: Commit at wrong place.` when called at
`CurrentDepth > 0`, and its own failure path collapses the envelope
(depth 1 -> 0) before propagating, so no save occurs either way. The fix
guards the existing line-326 call so a raise there cannot skip line 332.

### C2 -- P1 surface: expose both `HasOpenSessionTask()` and `CurrentDepth`

Both are added to `FLExProject`, per `reviews/cycle1-domain.md` Q1/Q3.
`CurrentDepth` is a raw `int` passthrough (already a de facto documented
escape hatch -- read via `getattr(...,0)` at the three existing internal call
sites, and reasoned about in prose in `AbortSession`'s own docstring).
`HasOpenSessionTask()` is the higher-level, common-case question.

### C3 -- `HasOpenSessionTask()` is scoped narrowly, not mode-agnostic

`HasOpenSessionTask()` answers exactly "is the session-long
`BeginNonUndoableTask()` envelope currently open?" -- it does not try to
be a mode-agnostic "is anything open" predicate (depth=1 means two
structurally different things per mode). Under `undoable=True` the envelope
never exists by construction, so the answer is unconditionally `False` --
a correct fact, not "nothing to report."

### C4 -- Return contract at the edges (accepted from domain paper Q2)

- **`writeEnabled=False` (read-only):** return the real value, do not raise.
  `CurrentDepth` is legitimately `0` and `HasOpenSessionTask()` legitimately
  `False` -- a pure read has no mutating consequence, so `FP_ReadOnlyError`
  would be domain-wrong here.
- **Project closed / never opened (`self.project` does not exist):** raise
  `FP_ProjectError` (reusing the existing lifecycle exception; there is no
  `FP_ProjectNotOpenError` in `exceptions.py`). Returning a silent `0`/`False`
  here is exactly the failure mode P1 exists to prevent.

### C5 -- Depth-read consolidation: one private helper, lenient fallback stays out of the public surface

Consolidate the depth read itself ("read `ActionHandlerAccessor.CurrentDepth`
off a live LCM action handler") into one private helper shared by the public
P1 surface and (optionally, at the implementer's discretion during T2) the
three existing internal call sites. The public `CurrentDepth` /
`HasOpenSessionTask()` must check "is the project actually open" first
(C4) and raise there; only past that guard does it call the shared depth
read. The three internal callers' `except: return 0` / `getattr(...,0)`
exists to tolerate incomplete test doubles, not to describe real LCM
behaviour, and must not be inherited into the public surface -- doing so
would make the public API silently return `0` for a closed/never-opened
project, reintroducing the exact ambiguity P1 removes.

### C6 -- P0's guard consumes P1: this is a dependency, not a sequencing preference

`CloseProject()`'s line-326 call is unconditional today -- it never checks
whether an envelope is actually open. Per `reviews/cycle1-domain.md` Q5, the
fixed `CloseProject()` must:

1. Check `HasOpenSessionTask()` (or `CurrentDepth > 0`) before attempting
   `EndNonUndoableTask()`. If no envelope is open, skip the call with a
   debug log rather than assuming the mode implies the envelope's presence
   (this also covers the case where a prior `AbortSession()`'s envelope
   reopen itself failed -- see `AbortSession()`'s own `FP_ProjectError`
   path, `FLExProject.py:790-796`).
2. Even when the depth check says an envelope IS open, still wrap the
   `EndNonUndoableTask()` call itself in a guard (try/except or try/finally)
   so that an unexpected raise there cannot prevent `usm.Save()` at line 332
   from running.

Both halves are required: the depth check handles the known forcing
condition (P-3's double-End); the wrap handles any other unexpected raise
from the same call without assuming the depth check is exhaustive. P1
(the depth-read surface) is therefore a prerequisite of P0's final shape,
not an independent follow-on ask -- `tasks.md` sequences accordingly.

### C7 -- End-then-Save order is unchanged

The fix does not reorder lines 326/332. End-then-Save remains correct; only
the guard around End changes.

### C8 -- P2 content is owned by `/lex-doc`, not authored here

Per the Archivist/Doc-Agent division of labour, this spec states that a
CHANGELOG entry is required and what it must cross-reference (the `[4.4.0]`
`undoable` default-flip entry, and this fix); it does not author the entry's
prose. See `tasks.md` for the dispatch task.

### C9 -- Q1 RECONCILED: the owner's incident is a P-5 -> P-3 CHAIN, and the C6 guard covers it

Ruled by `/lex-lead` 2026-09-07, closing Q1 (see "Open questions" below).
P-5 and P-3 are NOT competing hypotheses for the owner's incident -- they
are the two halves of one sequence, and the probe measured both halves
live:

1. **Trigger (P-5).** `SaveChanges()` (`FLExProject.py:563-588`) calls
   `usm.Save()` with no depth check. Under `undoable=False` the
   session-long envelope holds `CurrentDepth` at 1 for the whole session,
   and the P-2 table confirms `Transaction()` never changes it. So a
   mid-session `SaveChanges()` reaches `usm.Save()` at depth 1 -->
   `InvalidOperationException: Commit at wrong place.` (the owner's exact
   `[WARN]` string), AND `CheckReadyForCommit`'s failure path collapses the
   envelope, depth 1 --> 0, as a measured side effect.
2. **Loss mechanism (P-3).** With the envelope now collapsed, the
   unconditional `EndNonUndoableTask()` at line 326 has nothing to end -->
   `Cannot end task that has not been started.` --> line 332's `usm.Save()`
   is skipped --> the whole session's in-memory work is discarded.

The mutations are still in the in-memory cache at step 2 (non-undoable mode
rolls nothing back -- `OpenProject`'s own one-shot warning says so), so
step 2 is where the data is actually lost, and step 2 is exactly what the
C6 guard prevents: the depth check reads 0, skips the End, and reaches
`usm.Save()` at a legal depth.

**This is why no owner repro steps are needed.** The trigger is reachable
from flexicon's own SHIPPED DOCSTRING EXAMPLE: `SaveChanges()`'s docstring
(line 572) states "Does NOT call EndNonUndoableTask() - the session stays
open" and its Example block shows `with project.Transaction(...)` followed
by `project.SaveChanges()`. That example is correct under `undoable=True`
(depth 0 inside `Transaction()`, per P-2) and is a guaranteed
`Commit at wrong place.` under `undoable=False` (depth 1). The owner's
consumer-side remedy for the 4.4.0 default flip was to pass
`undoable=False` -- which moved their code onto the broken branch of that
example. Trigger, symptom string, single-`[WARN]` presentation and
total-loss outcome are all accounted for without asking the owner anything.

### C10 -- the `.fwdata` file-swap detail is OUT OF SCOPE and must not be claimed as fixed

Also ruled 2026-09-07, closing Q1's first half. The probe's P-6 finding
(`.fwdata` byte-for-byte unchanged, delta 0, no `.bak`/recovery sibling
created) is not a failure to reproduce the bug -- it is the CORRECT and
expected consequence of `usm.Save()` never running: nothing was written, so
nothing on disk could change. `CloseProject()` has no code path that
renames, rotates, truncates or replaces `.fwdata`, so no change within this
feature's scope can cause or prevent a file swap. The owner's observation
that `Target.fwdata` was later replaced by something sized exactly like the
old `Target.bak` is therefore attributed to a mechanism OUTSIDE flexicon
(FieldWorks' own crash-recovery / backup rotation reacting to the abnormal
state, or a restore), and is left unexplained by design rather than
investigated here.

Two binding consequences:

- **P2 (CHANGELOG, C8) must NOT claim this fix prevents the file
  replacement.** It fixes the loss of the in-memory session; it says
  nothing about on-disk file rotation. Overclaiming here would be the same
  category of error as the withdrawn root cause in section 4.
- No task in `tasks.md` may open an investigation into FieldWorks-side
  recovery behaviour. If a future reader wants that explained, it is a new
  issue against FieldWorks/liblcm, not this feature.

### C11 -- `HasOpenSessionTask()` reads depth BEFORE the mode check: lifecycle precondition outranks the mode short-circuit

Ruled by `/lex-lead` 2026-09-07 at the T1 review, resolving a genuine
conflict between C3 and C4 that the cycle-2 dispatch brief had papered over.
The brief said `HasOpenSessionTask()` should "return `False` WITHOUT
consulting depth" when `self._undoable` is `True`. **That wording was wrong
and is superseded by this decision.** The shipped implementation is correct:

```python
depth = self._ReadActionHandlerDepth()   # lifecycle precondition first
if self._undoable:
    return False                         # C3: unconditional in Phase 2
return depth > 0
```

Two independent reasons the read must come first:

1. **C4 would otherwise be violated in one mode.** C4 requires a
   closed/never-opened project to raise `FP_ProjectError` from BOTH members,
   with no mode carve-out. Short-circuiting on `self._undoable` before the
   read would make a closed `undoable=True` project answer `False` instead
   of raising -- silently returning a well-formed boolean for a project that
   does not exist, which is precisely the depth ambiguity P1 exists to
   remove (C5's reasoning, applied to the lifecycle axis instead of the
   fallback axis).
2. **The literal brief wording is not even implementable safely.**
   `FLExProject` has no `__init__`, and `OpenProject()` assigns
   `self.project` (line ~263) BEFORE `self._undoable` (line 271). On a
   never-opened instance neither attribute exists, so testing
   `self._undoable` first raises a bare `AttributeError` -- an
   implementation-detail exception escaping the public API instead of the
   documented `FP_ProjectError`.

**C3 is not weakened by this.** C3's requirement is that the ANSWER is never
derived from depth under `undoable=True`, and it is not: `depth` is read for
its raise-or-not effect only, then discarded unread on the Phase 2 branch.
Ordering a precondition check ahead of a mode short-circuit is not the same
thing as making the answer depth-dependent.

**Binding on future readers:** do not "fix" this back to the literal brief
wording, and do not reorder the mode check ahead of the read. The docstring
at `HasOpenSessionTask()` already states the rationale inline; if that
comment is ever removed, this decision still governs. Any change to this
ordering must cite and overturn C11 explicitly.

### C12 -- T2 is DROPPED. The three internal lenient call sites keep their own depth read, permanently

**Ruled 2026-09-07 by `/lex-lead` at the cycle-3 review. This supersedes C5's
"optionally, at the implementer's discretion during T2" clause: the option is
now CLOSED as declined.** Evidence:
`evidence/live-t2-internal-callsite-dedup.md`; finding:
`reviews/cycle3-programmer.md`.

T2 asked that `transaction.py:_current_depth`, `undoable_operation.py:102`
and `System/CustomFieldOperations.py:306` delegate to T1's
`_ReadActionHandlerDepth()` with each site's lenient fallback wrapped around
the call. All three were tried and each broke the offline suite (9 / 2 / 2
failures). T2 is dropped on the merits, not merely on cost. **Do not
re-attempt it.** Re-opening requires citing and overturning this decision.

**The premise was wrong.** T2 assumed the three lenient sites and the strict
public surface want the *same* read semantics and differ only in error
tolerance. They provably want *different contracts*:

- `_ReadActionHandlerDepth()` (C5) is deliberately STRICT -- it raises
  `FP_ProjectError` on a closed/never-opened project and returns the depth
  verbatim, so a caller can never confuse "no envelope" with "no project".
- The three internal sites are deliberately LENIENT -- they coerce any
  non-`int` to `0` so a malformed double degrades to "treat as outermost"
  rather than raising, as `transaction.py:_current_depth`'s own docstring
  states.

One implementation cannot serve both without one contract corrupting the
other. Sharing them is not a de-duplication; it is a conflation.

**Both escape hatches named in the cycle-3 report are REJECTED, and for a
stronger reason than the report gives.**

1. **`isinstance(depth, int)` after delegation -- REJECTED.** The report
   calls this a join-vs-open logic change. Precise correction, so this is not
   mis-cited later: in *production* it is behaviour-preserving (the helper
   returns a real `int`, so the coercion never fires). What it breaks is the
   *test doubles*, and it breaks them in a way that matters. The doubles
   configure `project.project.ActionHandlerAccessor.CurrentDepth = 1`
   explicitly, but mock the project *wrapper*; delegating routes the read
   through a new wrapper method the bare `Mock()` auto-vivifies, so the code
   reads an auto-stub instead of the value the fixture configured, and the
   `isinstance` guard then silently rewrites it to `0`. The refactor does not
   merely fail the tests -- it makes them stop testing what they claim to.
   **The decisive objection is separate and applies to production too:** the
   prescribed `except`-wrapper would swallow the `FP_ProjectError` the helper
   exists to raise (C5/C4) and substitute `0`. At
   `CustomFieldOperations.py:306` that `0` disables a corruption guard -- the
   issue-#21 guard that refuses `CreateField` inside an open UnitOfWork.
   Degrading a corruption guard to "no open UoW" because a *closed project*
   raised is strictly worse than three duplicated depth reads.
2. **Editing the static source-grep test -- REJECTED.** `tests/test_custom_field_create_refusal.py:54-60`
   asserts the literal substrings `"ActionHandlerAccessor"` and
   `"CurrentDepth"` remain in `CustomFieldOperations.py`. Verified present and
   deliberate: it pins the #21 guard's implementation, not just its output.
   Delegation removes both literals. Loosening a test that exists to pin a
   corruption guard, in order to reach a refactor whose stated upside is "zero
   functional delta", is net-negative. Satisfying it by leaving the strings in
   a comment would be gaming it and is equally rejected.
3. **Adding `spec=` to the doubles -- REJECTED as a means to T2.** Since T2
   itself is dropped on the merits, the test-suite change that would unblock
   it has no remaining purpose. It is NOT deferred and NOT a follow-up ask; no
   ticket is owed.

**Non-blocking observation, recorded so it is not rediscovered as a
surprise** (deliberately NOT a task, NOT an open question, NOT a filed
issue): the doubles in `tests/test_b1t_action_handler_double.py`,
`tests/operations/test_transaction_rollback.py` and
`tests/test_custom_field_create_refusal.py` use bare `Mock()`/`MagicMock()`
with no `spec=`, so they auto-vivify any attribute and cannot detect a
call-site change that reroutes a read through a new wrapper method. That is a
latent blind spot in those three files only. If a future feature independently
needs `spec=`-tightened project doubles it may do so on its own merits; issue
#243 does not.

---

## Open questions -- do not silently decide

### Q1 -- RESOLVED 2026-09-07 by `/lex-lead`: reconcile the probe with the owner's report

**No longer open. Ruled without owner input; see C9 and C10 above for the
binding decisions.** Summary of the ruling:

- **The `Commit at wrong place.` discrepancy is resolved, not merely
  flagged (C9).** P-5 is the TRIGGER and P-3 is the LOSS MECHANISM of a
  single chained sequence, not two rival explanations. A mid-session
  `SaveChanges()` under `undoable=False` raises `Commit at wrong place.`
  at depth 1 and collapses the envelope; the collapsed envelope then makes
  `CloseProject()`'s unguarded line-326 End raise, skipping line 332's
  `usm.Save()`. The C6 guard breaks the chain at its loss-bearing step.
  Both halves were already measured live in cycle 1 -- nothing new needed
  measuring to close this.
- **The owner's repro steps were not required** because the trigger is
  reachable from `SaveChanges()`'s own shipped docstring Example, which is
  valid under `undoable=True` and a guaranteed raise under `undoable=False`
  (C9). Asking the owner would have confirmed a path already proven
  reachable from the library's own documentation.
- **The `.fwdata` file swap is out of scope and stays unexplained (C10).**
  It cannot be caused or prevented by anything in this feature's fix
  surface, and P2 must not claim otherwise.
- **The P0 guard's design is unblocked and unchanged.** C1/C6/C7 stand
  exactly as frozen. This ruling did not alter the fix shape; it explains
  why that shape is the right one for the owner's actual sequence and
  raises T4's P-5 assertion from "does not compound the loss" to a measured
  survivor count (see `tasks.md` T4).

**Spawned follow-up, NOT in scope here (needs user approval to file).**
`SaveChanges()` has no depth guard, so under `undoable=False` it converts a
documented usage pattern into a liblcm exception that also destroys the
session envelope. Making `SaveChanges()` fail fast (or handle depth > 0)
is a fourth ask beyond section 3's three, and section 4 binds this feature
to those three. It is therefore routed to
`specs/tier1-silent-data-loss/QUEUE.md` --> "Awaiting user approval" rather
than absorbed here. What IS in scope: P2/`lex-doc` correcting the
`SaveChanges()` docstring Example so it stops recommending the broken
pattern (docs, not behaviour).

### Q2 -- What happens if `usm.Save()` itself raises after the P0 guard runs?

Today, if line 332's `usm.Save()` raises for any reason, `CloseProject()`
never reaches its own `self.project.Dispose()` at line 334 -- the probe's
own harness had to hand-roll `_dispose_if_open()` in test teardown to cope
with exactly this gap (P-3, P-5). Should the P0 fix also wrap the whole
`CloseProject()` body (or at least everything from line 326 onward) in a
`try/finally` that guarantees `Dispose()` always runs, even on a `Save()`
failure -- separately from the End-guard's own try/finally? Not decided;
left to the implementation cycle, informed by whichever answer Q1 produces.

### Q3 -- RESOLVED 2026-09-07 by `/lex-lead`: NO capability token

**CLOSED. The answer is NO** -- `HasOpenSessionTask()`/`CurrentDepth` do NOT
get a `flexicon.CAPABILITIES` token (no `session-depth-read` or equivalent),
and `flexicon/__init__.py` and `tests/write_path_transactions/test_capabilities.py`
are OUT OF SCOPE for this feature. Ruled in the cycle-2 dispatch and recorded
here so it cannot be relitigated after a context reset.

Rationale: `CAPABILITIES` earns its keep for behaviour a consumer cannot
otherwise detect without attempting a write (e.g. transaction/undo
semantics). A plain additive read member is detectable with a one-line
`hasattr(project, "HasOpenSessionTask")`, so a token would add a second,
independently-maintained source of truth for a fact the attribute already
states. Adding it would also widen T1's diff past `FLExProject.py` into
`__init__.py` plus the capabilities test, breaking the "one file, purely
additive" scope fence that makes T1 safe to land ahead of the P0 guard.

Verified honoured at T1: neither file appears in the changed-file list
(`git diff --stat flexicon/code/` = 120 insertions, 0 deletions, one file).

**Reopening condition (the only one):** if a real consumer is found that
cannot use `hasattr` -- e.g. a wire-protocol client that never touches the
Python object -- route it to `specs/tier1-silent-data-loss/QUEUE.md` as a
NEW ask needing user approval. Do not absorb it into this feature. T1's
report confirms no such consumer was encountered.

### Q4 -- Exact CHANGELOG placement and wording for P2

Whether the P2 entry lands under a new `[Unreleased]` heading or amends the
existing `[4.4.0]` entry with a forward pointer, and its exact prose, is
`/lex-doc`'s call per the Doc Handoff discipline (see C8) -- not decided
here.
