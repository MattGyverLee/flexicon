# SPEC -- 243-closeproject-save-guard

**Repo:** flexicon, branch `main`
**Issue:** #243 (`CloseProject()` unguarded `EndNonUndoableTask()` risks total
session loss)

> ## READ THIS FIRST -- #243's CEILING (frozen as C17, measured at T6) --
> **AND NOW MET, from the only side C17 said could ever meet it (T8b)**
>
> **No `CloseProject()`-side change could ever fix the owner's filed
> incident, at any price, and none did.** T6/P-7 measured the 25 entries
> as *already absent from the still-open project* immediately after
> `SaveChanges()` raised -- one full step **before** `CloseProject()` is
> ever entered. So no `CloseProject()`-side change -- not T3's shipped
> guard, not T7, not any future guard in that method -- could ever recover
> that data. **C17 named the only remaining route as the `SaveChanges()`
> depth guard, and T8b (spurt 7) shipped exactly that.** The full owner
> sequence -- create, mid-session `SaveChanges()`, `CloseProject()` -- now
> re-measures **25/25 in memory and 25/25 on disk**
> (`evidence/live-t8b-savechanges-guard.md`), where it measured 0/25 before
> T8b. C17's CEILING STATEMENT REMAINS TRUE AS WRITTEN -- it was never
> about whether the incident could be fixed at all, only about which
> method could fix it -- and this is exactly the outcome it predicted.
>
> **And, separately and unqualified: T3 IS a real fix for the P-3 path**
> (intact change set, stray/forced `End`): 0/25 -> 25/25, live-verified,
> shipped, untouched by the above. **Three things are simultaneously true
> and none may be collapsed into another:** (1) T3 fixed the independent
> P-3 mechanism; (2) no `CloseProject()`-side change could ever have fixed
> the owner's actual P-5 -> P-3 chain; (3) T8b, on the `SaveChanges()` side
> C17 pointed at, has now fixed that chain too. Full reasoning: **C16**
> (mechanism), **C17** (ceiling), **C20-C21** (the ruling and the guard
> shape that met it).

**Status:** CONTRACT FROZEN. Cycle-1 live probe complete. **T1 LANDED and
live-verified (spurt 2, cycle 2, 2026-09-07)** -- `flexicon/code/FLExProject.py`
now exposes the P1 depth-read surface (`_ReadActionHandlerDepth()`,
`CurrentDepth` property, `HasOpenSessionTask()`); the diff is purely additive
(120 insertions, 0 deletions, one file), so `CloseProject()` (T3) and
`SaveChanges()` are provably untouched. T2 is deliberately deferred to its own
gated sub-checkpoint (CP-A2) and CP-A is therefore only half done.
Q3 is now CLOSED (see Q3 below); Q2 and Q4 remain open.
**AS OF SPURT 8 (cycle 8, 2026-09-07) this paragraph is out of date on
progress -- read it as history and take the current state from below.**
Landed since: **T3+T4** (spurt 4, the P0 guard, CP-B PASSED), **T6**
(spurt 5, the no-op-save mechanism probe -- zero `flexicon/` diff), and
**T8a+T8b** (spurt 6/7, the `SaveChanges()` depth guard itself -- the
owner's filed incident now measures 25/25, see the banner above). Contract
is now **C1-C30**. Q2 CLOSED (C15). Q3 CLOSED (no capability token). Q4
CLOSED (spurt 8, `/lex-doc`'s placement/wording call). **Q5 fully
CLOSED** -- both its detector half (C18) and its ruling half (C20, the
user's ruling landing spurt 6). **T7 and T5b (spurt 8's docs pass) LANDED**;
**cycle 9 added C28/C29** on the cycle-8 QC audit's two P1 findings (the
`SaveChanges()` fail-open catch, and the `transaction.py` counter-measurement
to P-11) and opened **T9** (see `tasks.md` CP-CLOSE) as the one remaining
task before item 1 can close. **The ralph loop remains
CANCELLED** -- nothing resumes automatically; each spurt since spurt 5 has
been a directed dispatch, not a loop iteration.
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

### C13 -- What the T4 P-5 measurement DOES and DOES NOT establish

Ruled by `/lex-lead` 2026-09-07 (spurt 4, cycle 4). **T3's guard is confirmed
CORRECT by this measurement and needs no rework** -- C1, C6 and C7 all stand.
Three facts are frozen below; one asserted mechanism is explicitly NOT.

**FROZEN as established:**

1. **The "the guard skipped an `End` that should have run" hypothesis is
   DISPROVED, by measurement inside the same run.** The P-5 probe
   force-calls `EndNonUndoableTask()` manually immediately before
   `CloseProject()`, and that forced call **still raised** `Cannot end task
   that has not been started.` The envelope was genuinely gone, so an `End`
   could not have succeeded whether the guard attempted it or skipped it.
   **T3's fix shape is therefore not implicated by the 0/25 result** -- do
   not re-litigate C1/C6/C7 on the strength of it.
2. **Black box, measured live:** after a failed mid-session `SaveChanges()`
   at `CurrentDepth=1`, `CloseProject()` reaches `usm.Save()` at depth 0,
   does NOT raise, and 0/25 objects persist across a read-only reopen.
3. **Therefore `usm.Save()` returned successfully having persisted
   nothing.** `CloseProject()`'s `usm.Save()` call is bare -- there is no
   `try/except` around it -- so any raise there would have propagated out of
   `CloseProject()`. This is a sound INFERENCE, not a direct measurement, and
   it rests on fact 2's "did not raise", which T4 recorded in prose but **did
   not assert**: `test_p5_save_before_forced_end` captures `close_exc_msg`
   and never checks it, whereas `test_p3_p6_reproduction_and_symptom` asserts
   `close_exc_msg is None`. **T6 must close that gap before T7's remedy is
   built on it.**

**SUPERSEDED IN PART, 2026-09-07 (spurt 5, cycle 5): the "NOT frozen"
paragraph below has been ANSWERED by T6 and is now frozen as C16, and its
scope consequence as C17.** Read the paragraph below as the historical
statement of the open question, and **C16/C17 as the answer**. What survives
unchanged: the three FROZEN facts above, and the ban on citing the cycle-4
report's own asserted internals mechanism (*"the `UnitOfWorkService` cannot
commit after a failed `CheckReadyForCommit`"*) -- that specific wording is
still not established, because C16 confirms mechanism (ii)/(iii)'s *loss
point*, not the cycle-4 claim about the service's post-failure commit
capability, which P-8 in fact **contradicts** (a fresh envelope commits
fine).

**NOT frozen -- do NOT cite as settled:** *"the `UnitOfWorkService` cannot
commit after a failed `CheckReadyForCommit`."* That is a claim about liblcm
INTERNALS inferred from a single black-box survivor count. At least three
rival mechanisms produce identical observations:

- **(i)** the UOW / `UndoStack` is poisoned and refuses to commit for the
  rest of the session (the claim as written in cycle 4);
- **(ii)** `SaveChanges()`'s failure path DISCARDED the pending change set,
  so the loss already happened before `CloseProject()` was entered and there
  was nothing left for `usm.Save()` to write;
- **(iii)** collapsing the envelope unregistered the dirty objects from any
  commitable unit of work, so `usm.Save()` correctly flushed an empty change
  set.

Distinguishing **(ii)** from (i)/(iii) is decisive for scope, not academic:
**under (ii) the data is already gone when `CloseProject()` is entered, so no
`CloseProject()`-side change could ever reach 25/25** -- which settles
whether #243 alone could ever fix the owner's sequence. Routed to **T6**.
Freezing an unproven internals mechanism would be the same failure mode
`CLAUDE.md` warns about for same-name LCM fields: inferring a target's
behaviour from one adjacent observation.

**Bearing on the user's pending ruling:** all three mechanisms imply the SAME
shape for the queued fourth ask (make `SaveChanges()` refuse to call
`usm.Save()` at `CurrentDepth > 0`, failing fast before any damage occurs).
So the mechanism uncertainty does NOT block the user's decision on whether to
approve that ask; it only bounds what #243 may claim without it.

### C14 -- T3's quiet path is a NEW silent-loss surface, and closing it is IN SCOPE for #243

Ruled 2026-09-07 (spurt 4, cycle 4). For the owner's actual P-5 -> P-3 chain
(C9), T3 changes the outcome as follows:

| | data | signal on the close path |
|---|---|---|
| before T3 | 0/25 lost | `CloseProject()` **RAISED** |
| after T3 | 0/25 lost | `CloseProject()` **returns normally**; one `debug` line |

The loss is identical, and the only signal on the close path was removed. On
the P-3 path (a stray or forced `End` with an INTACT change set) T3 is a
genuine and complete fix -- 0/25 -> 25/25 -- and that stands unqualified. But
on the path C9 names as the owner's REAL incident, T3 is an **observability
regression**, and observability is the filed complaint verbatim: *"the only
symptom logged was a single `[WARN] Commit at wrong place.`"* Post-T3 the
close path is quieter than that. We have not made the loss worse; we have
made the SILENCE worse, on precisely the path this campaign is named after.

**The instruction was wrong, not the implementation.** `tasks.md` T3 said
"skip the call and log at debug level" and the programmer followed it
exactly. But in Phase 1 (`writeEnabled and not _undoable`),
`HasOpenSessionTask()` reading `False` inside `CloseProject()` is **anomalous
by construction**: the envelope is opened at `OpenProject()` and the frozen
P-2 table shows depth holds at 1 for the whole session. Reaching that branch
therefore means the envelope was already destroyed -- i.e. we are standing
inside the owner's incident. Logging that at the quietest level available and
returning normally is the defect. Same class as C11: a brief-wording error
owned by `/lex-lead`, not a programmer deviation.

**Remedy = T7**, in `flexicon/code/FLExProject.py` only, `SaveChanges()` NOT
touched:

1. the Phase-1 `else:` branch logs at **ERROR**, not `debug`;
2. `CloseProject()` still ALWAYS attempts `usm.Save()` (C1/C6 stand -- it is
   never skipped), and then **refuses to return normally** when it has
   detected that the save cannot be trusted: raise `FP_ProjectError` stating
   explicitly that the session's changes may not have been written to disk,
   and naming the anomaly. Attempt everything, THEN fail loudly;
3. detector, chosen by T6/P-9: prefer a live `IUndoStackManager`
   still-has-unsaved-changes read taken after `Save()`
   (mechanism-independent -- it detects any no-op save); fall back to the
   Phase-1-envelope-missing anomaly, already computable from T1's P1 surface;
4. T4's P-5 assertions are re-pointed at the new contract (`CloseProject()`
   RAISES on the P-5 sequence; survivors stay 0/25) and gain the
   `close_exc_msg` assertion C13 fact 3 shows is missing.

**This remedy restores LOUDNESS, not DATA.** It makes total loss impossible
to miss. It cannot make the owner's sequence save -- only the queued
`SaveChanges()` fourth ask can do that. T5's CHANGELOG must say exactly that
and must not overstate it (same discipline as C10).

### C15 -- Q2(a) RESOLVED: `Dispose()` moves into a `try/finally`

Ruled 2026-09-07 (spurt 4). Q2's original question -- should
`CloseProject()`'s body get a `try/finally` so `Dispose()` always runs? --
was correctly left OPEN by T3, whose scope genuinely did not force an answer,
and it was not silently decided in any of spurts 1-3. **C14 forces it now:**
T7 makes `CloseProject()` raise after attempting `usm.Save()`, and a raise
emitted at that point must not leak the live LCM handle, so
`self.project.Dispose()` / `del self.project` move into a `finally`. RESOLVED
as a consequence of C14, not deferred a fourth time. The probe harness's
hand-rolled `_dispose_if_open()` teardown (cited in Q2's original text)
becomes belt-and-braces rather than load-bearing -- leave it in place.

### C16 -- C13's mechanism question is ANSWERED: (ii) CONFIRMED, (i) RULED OUT, (iii) INDISTINGUISHABLE from (ii) and left unresolved BY DESIGN

Ruled 2026-09-07 (spurt 5, cycle 5) by `/lex-lead` on T6. Evidence:
`evidence/live-t6-noop-save-mechanism.md`; report:
`reviews/cycle5-programmer.md`. T6 changed **zero** lines of `flexicon/`
(`git diff --stat -- flexicon/` empty, independently re-verified), so this
verdict is ruling-independent, as designed.

**(ii) is CONFIRMED -- by measurement, not inference.** P-7 re-read the 25
`TEST_p7_` entries from the **STILL-OPEN** project immediately after
`SaveChanges()` raised at `CurrentDepth == 1`, *before* `CloseProject()` was
ever called: **0/25.** The pending change set was not merely uncommitted --
it was already absent from `LexEntry.GetAll()` one full step before
`CloseProject()`'s own code runs.

**(i) is RULED OUT.** P-8 opened a **fresh** `BeginNonUndoableTask()` /
`EndNonUndoableTask()` pair *after* the failure, created one entry inside it,
and that entry persisted (**1/1**) in the same process, same `usm`, same
session, while the pre-existing dirty set stayed at 0/25. The
`UnitOfWorkService` is **not** globally poisoned. Note this also
**contradicts** the cycle-4 report's asserted wording that the service
"cannot commit after a failed `CheckReadyForCommit`" -- it can; only the
change set in flight at the moment of failure is unrecoverable.

**(iii) is NOT separately distinguishable from (ii), and that is recorded as
unresolved -- not tidied into certainty.** P-7's observation ("the objects
are gone from `LexEntry.GetAll()`") is equally consistent with "the change
set was discarded" (ii) and "the objects were unregistered from any
commitable unit of work" (iii). Both name the **same loss point** (inside or
immediately after the failed `SaveChanges()`, before `CloseProject()` is
entered) and therefore the **same scope conclusion** (C17), so nothing in
this campaign turns on the difference. The T6 report said so itself rather
than guessing, which is the correct outcome and is accepted as such.

**Binding on future readers:** cite this as "(ii) confirmed, (i) ruled out,
(ii)-vs-(iii) undetermined and decision-irrelevant." Do **not** upgrade it to
"(ii) proven and (iii) excluded". Splitting (ii) from (iii) would require
instrumentation **inside liblcm**, which is outside this project's reach; if
anyone ever wants it, that is a new issue against liblcm, not a task here
(same disposition as C10's `.fwdata` swap).

### C17 -- #243's CEILING: no `CloseProject()`-side change can EVER fix the owner's incident. Only the `SaveChanges()` fourth ask can

Ruled 2026-09-07 (spurt 5, cycle 5). **This is the single most important fact
in this feature.** It is stated in the spec header as well, deliberately
duplicated so a context reset cannot miss it.

**The consequence of C16's (ii)/(iii) loss point:** on the owner's real
P-5 -> P-3 chain (C9), the session's change set **never survives as far as
`CloseProject()`**. Therefore:

- **T3's shipped guard cannot recover that data.** Not a defect in T3 --
  C13 fact 1 already disproved the "the guard skipped an `End` that should
  have run" hypothesis by measurement, and C1/C6/C7 all still stand.
- **T7 cannot recover it either**, nor can any future guard, wrapper,
  retry, reorder or `try/finally` placed anywhere inside `CloseProject()`.
  The data is gone before that method is entered. T7 restores **loudness,
  not data** (C14) -- and C16 is now the *measured* proof of that, where
  C14 only had an inference.
- **The only place a fix for the filed incident can live is
  `SaveChanges()`** -- i.e. the campaign's still-unruled fourth ask
  (`QUEUE.md` -> "Awaiting user approval"). It is no longer a
  "would-also-help" improvement; it is the **only** thing that can fix the
  incident #243 was filed about.

**AND, equally binding, the other half:** **T3 is a genuine, complete,
shipped fix for the P-3 path** -- an intact change set plus a stray or forced
`End` -- measured 0/25 -> 25/25 with no raise, live, at CP-B. C17 does not
qualify, weaken or reopen that in any way. Anyone summarising this feature
must state **both** halves: *the P-3 loss mechanism is fixed; the owner's own
P-5 -> P-3 sequence is not fixable here at all.* Stating either alone is a
misrepresentation -- the first alone overclaims (C10's failure mode), the
second alone undersells shipped, verified work.

### C18 -- T7's DETECTOR: the envelope-missing anomaly is primary and required; `HasUnsavedChanges` is diagnostic-only and MUST NOT be over-claimed

Ruled 2026-09-07 (spurt 5, cycle 5) on T6/P-9, **resolving Q5's genuinely
open part**. This **supersedes C14 point 3**, which said to "prefer a live
`IUndoStackManager` still-has-unsaved-changes read taken after `Save()`
(mechanism-independent)". That preference is now measured to be **wrong** and
is withdrawn.

**What P-9 measured (all verbatim in the evidence file):** the live
`IUndoStackManager` (concrete `SIL.LCModel.Infrastructure.Impl.UnitOfWorkService`)
does expose `HasUnsavedChanges` (bool property). Read **immediately after**
`usm.Save()` it is `False` in BOTH the real-save case (25/25 persisted) and
the no-op case (0/25 persisted) -- **INDISTINGUISHABLE**. Read **immediately
before** the save it is `True` (real) vs `False` (no-op) --
**distinguishable**.

**The ruling, which accepts the T6 report's recommendation and then goes
further than it:**

1. **The post-`Save()` read is REJECTED as a detector.** Measured
   indistinguishable. C14 point 3's preference for it is void.
2. **T7's primary detector is the Phase-1-envelope-missing anomaly**, already
   computable from T1's `HasOpenSessionTask()` surface -- exactly as the T6
   report recommends. **ACCEPTED.** In Phase 1
   (`writeEnabled and not _undoable`) a `False` there is anomalous by
   construction (C14), so it is a sound trigger.
3. **A pre-`Save()` `HasUnsavedChanges` read is permitted ONLY as a logged
   diagnostic value inside that already-anomalous branch. It MUST NOT gate
   the raise and MUST NOT create a second code path.** Two reasons, both
   from the measurements themselves:
   - **It is not independent information.** In the real-save shape it read
     `True` *only after a successful `EndNonUndoableTask()`* (the probe ends
     the envelope immediately before the read); in the no-op shape the End
     never succeeded. So pre-`Save()` `HasUnsavedChanges` is a proxy for
     *"did an End just succeed?"* -- a fact `CloseProject()` already knows
     **first-hand**, from the outcome of the End attempt it made itself. It
     adds no knowledge T7 does not already hold locally.
   - **It is not proven mechanism-independent**, as the report itself says:
     (i) was ruled out in this very run, so the signal was only ever
     observed under (ii)/(iii).
4. **The report's suggested message wording is REJECTED.**
   `HasUnsavedChanges == False` must **NOT** be worded as *"and there is
   nothing pending to save"*. **Proven false-negative in this run:** in the
   no-op shape `HasUnsavedChanges` read `False` **before the trigger
   `SaveChanges()`**, at a moment when all 25 entries demonstrably still
   existed in memory (P-7 measures them present until `SaveChanges()`
   raises). The property means *"a completed-but-unsaved unit of work is
   registered"*, **not** *"dirty data exists"*. Wording it the other way
   would tell a user their data was never at risk at the exact moment they
   lost 25 objects -- the same category of overclaim C10 and C14 exist to
   prevent.

`tasks.md` T7 point 3 is re-scoped to match, so an implementer arriving after
a context reset cannot over-claim the detector.

### C19 -- T5 stays gated on the ruling, but is SPLIT: a minimal `[Unreleased]` stub (T5a) is separable and recommended NOW; the prominent release note (T5b) waits

Ruled 2026-09-07 (spurt 5, cycle 5), answering "is T5 still correctly gated
last?" with **yes for T5b, no for the whole of T5**.

**The costing that forces the split.** `CHANGELOG.md` carries a live
`[Unreleased]` section that already accumulates breaking behavioural changes
(e.g. #254) until a version cut. T3 is **already committed to `main`** and
therefore already inside that unreleased window **with no entry at all**.
That is the *worst* of the available states: if a version were cut today,
consumers would receive a behaviour change to a shipped public method --
including C14's observability regression -- entirely undocumented. "Defer all
of T5" is not a neutral hold; it is an active choice to leave a shipped
data-loss-adjacent change unnoted.

- **T5a -- minimal `[Unreleased]` stub, RECOMMENDED, ruling-independent.**
  Note T3 only, scoped exactly per C17's two halves: the P-3 path is fixed
  (0/25 -> 25/25), the `SaveChanges()`-at-depth>0 path is **not** fixed and
  `CloseProject()` currently **returns normally** there. This is a
  description of **shipped behaviour**, so it commits the project to no
  position on the fourth ask -- and it discloses nothing that public issue
  #243 does not already state. **Churn cost is zero:** the entry sits under
  `[Unreleased]`, so if T7 later flips that path to raise, the entry is
  edited before any version cut and nothing published ever churns.
  Constraints: C10 (no `.fwdata` claim), C17 (both halves), C14 (loudness
  not data). **Offered as a second pre-authorised, ruling-independent unit
  -- the user's to greenlight, exactly as T6 was.**
- **T5b -- the prominent P2 release note + the `SaveChanges()` docstring
  correction + Q4's placement/wording, STAYS GATED** behind the user's
  ruling and T7. Unchanged reasoning: its wording depends on both, and the
  docstring correction must tell callers what to do instead -- which depends
  on whether `SaveChanges()` is getting a guard.

**Not ruled here, and deliberately so:** whether T5a is *done* is the user's
call, not the loop's. This decision only establishes that it is *separable*
and that deferring it has a real, named cost.

### C20 -- the user's ruling, operationalised: the fourth ask is APPROVED IN SUBSTANCE, constrained to depth/transaction correctness, not sharing exclusivity

Ruled by the user directly, verbatim: *"resolve #243 with /lex-lead . The
goal is safe writes, but without sacrificing edits on shared projets.
editing custom fields is the only edit i've seen that CAN'T be done
shared."*

**(a) is APPROVED IN SUBSTANCE:** `SaveChanges()` gets a depth guard so it
fails fast instead of destroying the change set at `usm.Save()`. Per **C16**
the loss happens inside `SaveChanges()`, so this is the only place the filed
incident can be fixed.

**THE CONSTRAINT is transaction/depth correctness ONLY.** The guard must NOT
be implemented by requiring exclusive access, taking a lock, or refusing
writes because a project is shared (Send/Receive, LAN-shared, multi-user).

**PREMISE CORRECTION, verified against the code:** flexicon contains ZERO
sharing-based refusals. A sweep of `flexicon/code/` finds the only
shared-mode reference is `RefreshFromDisk()`'s docstring at
`FLExProject.py:772`, which is shared-project SUPPORT, not a refusal. The
custom-field refusal the user names is `CustomFieldOperations.py:306`,
`getattr(action_handler, "CurrentDepth", 0) > 0` -- a DEPTH refusal tied to
the issue #21 ghost-field corruption, not an exclusivity refusal. It
therefore does not carve out the exception it appears to; read the other
way, the guard the user already accepts is the same kind of guard the
fourth ask proposes.

**THE CONSTRAINT'S ONE CONCRETE HAZARD:** a blanket `CurrentDepth > 0`
refusal in `SaveChanges()` would refuse the second half of flexicon's own
documented shared-project recovery workflow (`RefreshFromDisk()`'s shipped
example is `RefreshFromDisk()` then `SaveChanges()`). Whether that hazard is
real is measured at T8a/P-10, and the guard's resulting shape will be frozen
separately as **C21**.

**Task numbers:** T8a = the P-10 measurement; T8b = the guard plus the T4
P-5 assertion flip.

### C21 -- SaveChanges() guard shape: a BLANKET predicate with a mode-differentiated MESSAGE

Ruled 2026-09-07 (spurt 7, cycle 7) by `/lex-lead` on T8a/P-10. Evidence:
`evidence/live-t8a-savechanges-depth-blast-radius.md`; report:
`reviews/cycle6-programmer.md`.

**The predicate is a blanket `CurrentDepth > 0` inside `SaveChanges()`.** No
mode exemption. Raises `FP_TransactionError`. If the depth read itself
raises (a closed/never-opened project, per C4/C5), the guard fails OPEN --
log a WARNING and proceed to the existing `usm.Save()` call, mirroring the
`getattr(action_handler, "CurrentDepth", 0)` leniency precedent at
`CustomFieldOperations.py:306`.

**Domain's cycle-6 Q4 recommendation -- condition the guard on `undoable`
mode, exempting the `undoable=False` session-envelope depth of 1 -- is
REJECTED.** It reasoned from the shipped docstring/prose account of the
`RefreshFromDisk()` -> `SaveChanges()` recovery workflow. P-10 measured the
metal instead. Across every path P-10 exercised -- P-5, P-7, and P-10's own
cases A and C -- there is no measured path in which `SaveChanges()` succeeds
at `CurrentDepth > 0`. Case B (the only success) is at depth 0, where the
guard never fires regardless of mode. **You cannot sacrifice a call that has
never once worked; refusing it earlier converts a destructive failure into a
safe one.**

**Q4's recovery-workflow hazard -- the one concrete hazard C20 named for the
constraint -- is DISCHARGED, twice:**

1. The second line of that exact sequence (`RefreshFromDisk()` then
   `SaveChanges()` under `undoable=False`) is already a guaranteed raise
   today, and that raise also destroys the session's pending work
   (P-5/P-7/P-10 case C, all measured 0/25). The guard does not turn a
   working recovery into a failing one; it turns an already-failing,
   already-destructive recovery into a failing, non-destructive one.
2. `RefreshFromDisk()` itself is untouched by this guard (it does not call
   `SaveChanges()` or read `CurrentDepth`), and the project's actual save
   still happens at `CloseProject()`'s `usm.Save()`, which runs only once
   `CloseProject()` has ended the `undoable=False` session envelope --
   i.e. after the envelope this guard checks has already closed.

**MESSAGE CLAUSE -- anti-overclaim discipline, same as C10/C14/C18 point
4.** The two `CurrentDepth > 0` cases the guard refuses are **not the same
event**, and the exception message MUST NOT conflate them:

- Under `undoable=False` (P-10 case C, matching P-5/P-7) the raw call
  **destroys the pending change set**: 0/25 survivors, measured
  independently three times.
- Under `undoable=True` inside an `UndoableOperation()` block (P-10 case A)
  the raw call **raises but the edit survives**: 25/25 in-memory AND 25/25
  on-disk after a genuine close-and-reopen, measured once.

**One predicate, two message bodies.** The `undoable=True` message MUST NOT
mention data loss or data risk -- saying so would tell a user their data was
at risk at a moment the measurement says it was not (C18's false-negative
discipline, applied here to a false-POSITIVE risk instead).

**Caveat to record, not resolved here.** Case A's survival depended on the
guard's `FP_TransactionError` being caught inside the `with
project.UndoableOperation(...)` block (P-10's harness used `_safe()` for
exactly this reason). If the guard's exception instead ESCAPES the block,
`UndoableOperation.__exit__` will treat it as a rollback trigger -- identical
to today's behaviour with the raw liblcm exception, so this is **not a
regression**, but it is being MEASURED as a new probe, **P-11**, inside T8b,
not inferred from P-10.

**Docstring corrections are IN T8b, not deferred.** Three shipped docstring
`Example` blocks are guaranteed refusals under `undoable=False` and are
corrected as part of T8b's diff, not routed to T5b: `SaveChanges()`
(`FLExProject.py` ~:745-750), `RefreshFromDisk()` (`FLExProject.py`
:792-797), and `AbortSession()`'s `else:` branch (`FLExProject.py` ~:908,
which calls `SaveChanges()`).

**Explicit unmeasured boundary.** Nothing in this feature may claim that
`RefreshFromDisk()` followed by `CloseProject()` fully recovers a
pending-reconciliation-wedged shared-project session. That claim needs a
second live client concurrently modifying the same project, has not been
measured, and is out of this feature's reach.

### C22 -- Test blast radius: the 11 affected pins, and the public-API / liblcm-mechanism split

Ruled 2026-09-07 (spurt 7, cycle 7) by `/lex-lead`. The full pin set was
enumerated up front rather than discovered mid-implementation.

**Verification note (reconstructed, not copied).** This dispatch's payload
to `/lex-doc` did not include the literal 11-site table `/lex-lead` is
reported to have enumerated in the parallel programmer brief and the
cycle-7 lead message; `/lex-doc` has no `Read` access to either channel
beyond what its own task prompt supplied. The table below was built
independently by grepping every live call site of `SaveChanges()` under
`tests/` and reading each one directly. It confirms the three details named
in the dispatch (probe `:658`'s written invitation,
`TestSaveChangesIsUnusableInThisMode`'s written invitation, and
`test_transaction_honesty.py:73`'s hardcoded 1000-character window) and
arrives at the same count, 11. If `/lex-lead`'s own enumeration differs in
any row, that version is authoritative and this table must be corrected to
match it -- see the cycle-7 doc report.

| # | Site | Current pin | Category | T8b disposition |
|---|---|---|---|---|
| 1 | `test_issue243_closeproject_probe.py:555` (`test_p5_save_before_forced_end`) | calls `project.SaveChanges()` at `CurrentDepth==1` | public API | keep calling `SaveChanges()`; now raises `FP_TransactionError`, not `InvalidOperationException` |
| 2 | `test_issue243_closeproject_probe.py:598-606` (same test) | asserts the raw `"Commit at wrong place."` string | public API | re-point at `FP_TransactionError`'s message |
| 3 | `test_issue243_closeproject_probe.py:658` (same test) | `assert surviving_count == 0` | public API | **explicit written invitation to flip** (comment: "25/25, if `SaveChanges()` itself is ever guarded per the QUEUE.md follow-up") -- flip to 25/25 |
| 4 | `test_issue243_closeproject_probe.py:725-732` (`test_p7_data_survives_failed_savechanges_in_memory`) | calls `project.SaveChanges()`, asserts `"Commit at wrong place."` | **liblcm mechanism** (P-7 is C16's mechanism evidence) | switch to the raw `usm.Save()` accessor so C16's basis is not silently deleted |
| 5 | `test_issue243_closeproject_probe.py:844-850` (`test_p8_fresh_entry_after_failed_savechanges`) | calls `project.SaveChanges()`, asserts the raw string | **liblcm mechanism** (P-8 is C16's (i)-ruled-out evidence) | switch to raw `usm.Save()` |
| 6 | `test_issue243_closeproject_probe.py:1032-1040` (`test_p9_iundostackmanager_detector`, TRIGGER call) | calls `project.SaveChanges()`, asserts the raw string | **liblcm mechanism** (P-9 is C18's detector evidence) | switch to raw `usm.Save()` |
| 7 | `test_issue243_closeproject_probe.py:1057-1058` (same test, NO-OP second call) | calls `project.SaveChanges()` again to mirror `CloseProject()`'s internal `usm.Save()` | **liblcm mechanism** | switch to raw `usm.Save()` |
| 8 | `test_issue243_closeproject_probe.py:1278` + `:1548-1612` (`test_p10_savechanges_depth_blast_radius`, case A) | calls `project.SaveChanges()` inside `UndoableOperation()`, asserts the raw string and 25/25 survival | public API (P-11's home) | keep calling `SaveChanges()`; re-point the exception assertion at `FP_TransactionError`; survival assertion (25/25) UNCHANGED |
| 9 | `test_issue243_closeproject_probe.py:1278` + `:1521,1542` (same test, case C) | calls `project.SaveChanges()` inside `Transaction()` under `undoable=False`, asserts the raw string and 0/25 | public API | keep calling `SaveChanges()`; re-point exception assertion at `FP_TransactionError`; the 0/25 outcome is now prevented before the call reaches liblcm at all |
| 10 | `test_abort_session_live.py:234-266` (`TestSaveChangesIsUnusableInThisMode`) | calls `target_sandbox.SaveChanges()`, asserts `System.InvalidOperationException` with `"Commit at wrong place"`; docstring: **"This test asserts the CURRENT broken behavior... It must be inverted when the defect is fixed."** | **liblcm mechanism, with an explicit written invitation to flip** | switch the mechanism assertion to the raw `usm.Save()` accessor (preserving what this test actually pins); add a new assertion that the public `SaveChanges()` now raises `FP_TransactionError` before reaching liblcm at all |
| 11 | `test_transaction_honesty.py:73` | hardcoded `source[save_idx : save_idx + 1000]` slice asserting accessor-pattern strings inside `SaveChanges()`'s body | **collateral, OFFLINE** | not a `SaveChanges()` caller -- it greps `FLExProject.py`'s source text. The guard clause plus the corrected docstring push the asserted substring toward/past the 1000-character window. Fix: widen the slice, do not shrink the guard/docstring to fit it. |

**Two rulings to state plainly, independent of the exact row wording
above:**

1. **NOT ONE affected pin was wrong.** Every one is a correct measurement
   of the pre-guard world. Two of them -- row 3 (probe `:658`) and row 10
   (`TestSaveChangesIsUnusableInThisMode`'s own docstring) -- were written
   with an explicit invitation to be flipped by exactly this change.
2. **Public-API tests keep calling `SaveChanges()`; liblcm-MECHANISM
   probes (P-7/P-8/P-9, rows 4-7) switch to the raw `usm.Save()`
   accessor.** Reason: P-7/P-8/P-9 are the measured basis of C13, C16 and
   C18. Rewriting them to assert `FP_TransactionError` instead of
   observing `usm.Save()` directly would silently delete that basis from
   the suite -- the new guard changes what USERS can reach, not what
   liblcm itself does once reached. Row 10 gets both treatments: the
   mechanism assertion moves to raw `usm.Save()` and a new assertion is
   added for the public `FP_TransactionError` path (the "flip" its
   docstring invited).

`test_transaction_honesty.py:73`'s hardcoded 1000-character source slice
(row 11) is collateral: the guard clause plus the docstring correction push
the asserted string out of the window and break an OFFLINE test. Named here
in advance so it is not discovered mid-implementation.

### C23 -- T7 recut: the `FP_ProjectError` raise is WITHDRAWN; the ERROR log is the whole remedy

Ruled 2026-09-07 (spurt 7, cycle 7) by `/lex-lead`. Post-T8b, the only
routes into `CloseProject()`'s Phase-1 `else:` branch
(`HasOpenSessionTask()` reads `False` while `writeEnabled and not
_undoable`) are:

1. **P-3** -- a stray or forced `EndNonUndoableTask()`, where the change set
   is intact and the save SUCCEEDS. Measured 25/25 at CP-B, unaffected by
   T8b.
2. **A failed `AbortSession()` reopen** -- already raises `FP_ProjectError`
   from `AbortSession()` itself (`FLExProject.py:955-963`), and the discard
   there was deliberate (the user chose to abort). Not this branch's
   problem to re-raise on.
3. **The P-5 route** -- `SaveChanges()` called mid-session at
   `CurrentDepth > 0`, collapsing the envelope and destroying the change
   set before `CloseProject()` is ever entered. **T8b CLOSES this route**:
   the blanket guard (C21) means `SaveChanges()` refuses at depth > 0
   instead of reaching `usm.Save()` and collapsing the envelope, so this
   path can no longer be reached the way P-5/P-7 measured it.

**So the only LIVE route left into the branch is the one where the data
demonstrably saved (route 1).** A raise there would fire as a **false
alarm on a successful close** and **never on a real loss** -- exactly
C18 point 4's prohibition (do not word a signal in a way the measurements
disprove), applied here to ourselves rather than to `HasUnsavedChanges`.

**Therefore:**

- **T7 point 2 (the `FP_ProjectError` raise) is WITHDRAWN.**
- **T7 point 1 (the ERROR-level log) SURVIVES** as the entire loudness
  remedy, reworded to: name the anomaly (`HasOpenSessionTask()` read
  `False` inside Phase 1, unreachable by construction unless something
  already ended the envelope early) and state plainly that `usm.Save()` is
  proceeding anyway -- asserting nothing about whether data was lost,
  because post-T8b this branch's live route is the one where it wasn't.
- **T7 point 3 (the detector, C18)** is unchanged in its own logic, but its
  consequence changes: it now feeds a LOG line, not a raise.
- **T7 point 4 (C15, `Dispose()` into `finally`)** survives untouched --
  independent of whether the branch raises or merely logs.
- **T7 point 5 is VOID.** T8b re-points the P-5 assertions itself (C22 row
  3), and to **25/25**, not to "raises, 0/25" -- there is no longer a
  T7-side assertion flip to make.

**C14 and C17 are NOT reopened by this.** C14's diagnosis that T3 created an
observability regression stands -- the branch really was quieter than it
should have been. C17's ceiling stands -- no `CloseProject()`-side change
was ever going to fix the owner's original filed sequence; it took a
`SaveChanges()`-side change (T8b) to do that. **Only C14's chosen remedy
SHAPE narrows**, and only because T8b removes the loss path C14's raise was
written to make audible.

**Addendum, 2026-09-07 (spurt 8, cycle 8): route-(1)'s reasoning above is
now MEASURED, not inferred.** `evidence/live-t8b-savechanges-guard.md`'s
"Phase-1 `else:` branch observation" section shows the Phase-1 `else:`
branch actually taken on a live P-5 re-run: `HasOpenSessionTask()` read
`False`, `EndNonUndoableTask()` was skipped, and the save SUCCEEDED --
25/25. `/lex-lead` separately considered and REJECTED downgrading the
branch's log level from ERROR to WARNING: WARNING is the exact severity
the original incident proved invisible at (`QUEUE.md` item 1: "the only
symptom logged was a single `[WARN] Commit at wrong place.` line"). C23
otherwise stands verbatim.

### C24 -- CHANGELOG factual correction: T8b closes the gap C13/C17 said could never close

Ruled 2026-09-07 (spurt 8, cycle 8) by `/lex-doc` on dispatch.
`CHANGELOG.md` (`[Unreleased]` -> `### Fixed`, the #243 entry) stated
verbatim: **"This does not fix the incident #243 was filed about."** That
statement is now FALSE on `main`: T8b's `SaveChanges()` depth guard
(C20/C21) closes the P-5 trigger before it can collapse the envelope, so
the full owner sequence (create, mid-session `SaveChanges()`,
`CloseProject()`) now re-measures **25/25 in memory and 25/25 on disk**
(`evidence/live-t8b-savechanges-guard.md`, P-10 case C / P-11), where it
previously measured 0/25 (C13/C16/C17). C19 pre-authorised this class of
edit -- the entry sits under `[Unreleased]`, so correcting it before any
version cut costs nothing. Three parts landed in `CHANGELOG.md`:

1. A new `### Changed` bullet classifying `SaveChanges()`'s raised
   exception-type change (liblcm `InvalidOperationException` ->
   `FP_TransactionError`) as a public-behaviour change, stating the
   per-mode remedy for callers.
2. The old paragraph (formerly at `:82`) replaced with the two-step
   chain -- `SaveChanges()` now refuses before `usm.Save()`, so
   `CloseProject()` reaches a legal-depth save with an intact change set
   -- and the 25/25 re-measurement.
3. A mandatory anti-overclaim clause carrying **two** carve-outs, not
   one: (i) C10's `.fwdata`-swap exclusion (still out of scope, unchanged
   by T8b), and (ii) a new single-client caveat -- every measurement
   cited is against a local, file-backed `target_sandbox_path` copy; no
   shared/multi-client recovery behaviour was measured or is claimed.

A fourth, separate paragraph notes T7 (landing in parallel this cycle):
the Phase-1 envelope-missing branch now logs at ERROR, not `debug`,
restoring loudness (C14) without asserting anything about data loss (C23).
`/lex-lead` verifies this paragraph against the landed diff next cycle.

**This corrects a statement that had already reached `main`.** Anyone
citing the pre-C24 CHANGELOG text as current is citing a claim this
decision supersedes.

### C25 -- P-11 routing: the measured 25/25 survival is the regression pin; the broader rollback-semantics question is OUT of #243's scope

Ruled 2026-09-07 (spurt 8, cycle 8). T8b's P-11
(`evidence/live-t8b-savechanges-guard.md`) measured, against its own
a-priori 0/25 prediction, that an `FP_TransactionError` escaping a `with
project.UndoableOperation(...)` block -- triggering
`UndoableUnitOfWorkHelper.Dispose()` + `set_RollBack(True)` -- did NOT
discard the 25 object creations made inside that block: 25/25 survived
both an in-memory re-read and a genuine close-and-reopen. Disposition:

- **The measured 25/25 stays as this feature's regression pin** (T8b's
  own test asserts the measured value, not the a-priori prediction).
- **A narrow, measured caveat** -- object creation inside an
  `UndoableOperation()` block has been measured to survive an escaping
  exception's rollback, contradicting that module's own docstring claim
  that rollback discards the block's mutations -- **lands in
  `undoable_operation.py`'s docstring; that is the programmer's diff, not
  this doc agent's.**
- **The broader question -- does `Dispose()`/`set_RollBack(True)`
  actually discard ANYTHING (property modifications, deletions: both
  unmeasured), and is `AbortSession()`'s advertised rollback semantics
  therefore also wrong -- is OUT of #243's scope.** Routed to
  `specs/tier1-silent-data-loss/QUEUE.md` -> "Awaiting user approval". NO
  work happens on it until the user approves; it is a candidate feature
  directory of its own.
- **This gates exactly one thing: T5b's `docs/TRANSACTION_GUIDE.md`
  wording** (the binding constraint there: do not claim an escaping
  exception safely discards work; do not generalise the 25/25 to property
  modifications or deletions). **It gates neither T7 nor T8b's own
  completion** -- #243's frozen contract (sections 3/4) never covered
  `UndoableOperation()` rollback semantics, so nothing here reopens
  C1-C23.

### C26 -- C22 table CORRECTION: re-keyed to `/lex-lead`'s authoritative 11-item enumeration

Ruled 2026-09-07 (spurt 8, cycle 8). C22's table above was independently
reconstructed by `/lex-doc` from a grep sweep (its own "Verification
note" says so) rather than copied from `/lex-lead`'s own cycle-7
enumeration. Both tables total 11 rows, but on comparison they are
**different partitions of the same test-blast-radius** -- the matching
COUNT is a coincidence, not agreement. Per C22's own escape clause ("If
`/lex-lead`'s own enumeration differs in any row, that version is
authoritative"), `/lex-lead`'s enumeration governs. Re-keyed here, with
C22's finer splits folded in as sub-rows:

| # | Site | Sub-rows from C22's table | Note |
|---|---|---|---|
| 1 | `test_abort_session_live.py:234-266` (`TestSaveChangesIsUnusableInThisMode`) | C22 row 1 | Inverted to assert `FP_TransactionError`; class docstring rewritten |
| 2 | `test_abort_session_live.py:121-123` (prose cross-reference) | **absent from C22's table** | Prose-only update (T8b disposition item 2) |
| 3 | probe `:593-606` (P-5 exception assertions) | C22 row 3, exception-assertion half | Now asserts `FP_TransactionError`, absence of `"Commit at wrong place."`, unchanged `CurrentDepth` |
| 4 | probe `:658` (P-5 `surviving_count`, the invited flip) | C22 row 3, survivor-count half | Flipped `== 0` to `== N_ENTRIES`; measured 25/25 |
| 5 | probe `:568-580` / `:608-635` (P-5 verdict prose) | **absent from C22's table** | Verdict prose reworded for the new contract (T8b disposition item 5) |
| 6 | probe P-7 `:693-760` | C22 row 4 | Trigger switched to raw `usm.Save()` accessor; mechanism assertions unchanged |
| 7 | probe P-8 `:817-894` | C22 row 5 | Same treatment as row 6 |
| 8 | probe P-9 `:1029-1058` (both calls) | C22 rows 6+7 | Same treatment; trigger call and no-op mirror call both switched |
| 9 | probe P-10 (cases A and C) | C22 rows 8+9 | Both re-pointed at `FP_TransactionError`; case A survival unchanged (25/25), case C survival CHANGED (0/25 -> 25/25) |
| 10 | `tests/test_transaction_honesty.py` (the source-slice windows) | C22 row 11, with its "(and `:154`)" parenthetical now DELETED -- see below | See ADDENDUM (item D) |
| 11 | `tests/manual_verification.py:487,526` | **absent from C22's table** | Line 526's finding string updated; line 487 an unaffected availability check (T8b disposition item 11) |

**Items 2, 5 and 11 were edited by the programmer (per
`evidence/live-t8b-savechanges-guard.md`'s item-by-item disposition) but
appear nowhere in C22's table.** That is the defect this correction
fixes: a later auditor diffing the landed change against C22's table
alone would find three unexplained edits.

**Row 11's old parenthetical "(and `:154`)" is DELETED from C22's table
text above.** At HEAD, line ~152 of `tests/test_transaction_honesty.py`
is inside `test_transaction_body_always_passes_none_none`, whose slice is
`source[txn_idx:save_idx]` -- unbounded on the `SaveChanges()` side, so it
is unaffected by anything that grew inside `SaveChanges()`'s body, and
was never touched by T8b.

**ADDENDUM (item D) -- the enumeration was site-complete but
REMEDY-incomplete.** Row 10 (`test_transaction_honesty.py`) needed
**two** source-slice windows widened, not one, both inside the single
test `test_uses_same_accessor_pattern_as_save_changes`, both broken by
the same cause (docstring growth ahead of the accessor call):

- `save_body`: `1000` -> `6000` chars (the window C22/the dispatch brief
  named).
- `refresh_body`: `2500` -> `4000` chars (adjacent in the same test,
  broken by `RefreshFromDisk()`'s docstring also growing under C21's
  Note-on-mode addition -- **not named in the original brief**, found
  only by running the suite after the first widening and watching it
  still fail).

**General rule, recorded for future test-blast-radius enumerations: when
a pin is a hardcoded source-slice window, enumerate EVERY bounded slice
in the enclosing test, not just the one the dispatch brief names.** A
test can carry more than one magic-width window, and they can share a
root cause without sharing a name.

**Recorded as P2 / optional / not-now, not a task:** these hardcoded
character-width windows (`save_body`, `refresh_body`, and any future
sibling) should eventually be bounded by the next `def ` in the source
file rather than a magic width, so future docstring growth cannot
silently re-break them. Not filed as a ticket; noted here so it is not
rediscovered as a surprise.

### C27 -- staleness ownership: whoever lands a spurt's docs task owns the sweep

Ruled 2026-09-07 (spurt 8, cycle 8). The doc agent landing a spurt's docs
task owns the staleness sweep of this feature's own prose tracking files
(`spec.md`, `tasks.md`, `STATUS.md`, and the campaign `QUEUE.md` entry) in
the SAME diff as the docs task itself. No spurt may close with a
top-of-file state summary (a banner, a "STATE AS OF SPURT N" block, a
queue status cell) that contradicts the record below it. If no docs task
runs in a given spurt, the owed sweep must be named EXPLICITLY in that
spurt's handoff so the next docs task (or a human) does not have to
rediscover it by reading the whole file.

**`.crew-handoff.json` is explicitly OUT of this scope** -- it is
machine-readable orchestration state, normally written by whoever lands a
spurt's checkpoint (`/lex-lead`/`/lex-archivist`), not prose documentation.
Doc-agent staleness sweeps do not extend to it; a doc agent that finds it
stale should flag it as a finding, not silently absorb its maintenance.

### C28 -- the SaveChanges() fail-open catch: breadth accepted, contract broadened, coverage added

Ruled 2026-09-07 (spurt 9, cycle 9) by `/lex-lead` on the cycle-8 QC audit's
P1 #1. The audit found the fail-open catch at `FLExProject.py:845-856`
(`except Exception as e: ... depth = 0`) is broader than its own
justification: C21's reasoning covers exactly ONE documented raise --
`FP_ProjectError` when `self.project` does not exist (C4/C5) -- but the code
catches ANY exception from the depth read, and no test, live or offline,
exercises the fail-open branch at all. P0 count was 0; this was a P1.

**RULED: the catch is NOT narrowed, and C21's fail-open policy is NOT
reopened.** Narrowing to `except FP_ProjectError` would require enumerating
every exception `ActionHandlerAccessor.CurrentDepth` could throw on a live
but degraded project object -- a set nobody has measured -- and would
convert every UN-enumerated exception into a NEW exception propagating out
of a public save method, on speculation about failure modes that have never
been observed. That is the same class of error as **C12** (a contract
invented for an unmeasured case) and **C11/C14** (behaviour changed off
brief wording rather than evidence): all three penalise the unmeasured case
by making a public method's behaviour worse on a guess.

**RULED: the mismatch closes the OTHER way, via the audit's own
alternative** -- broaden the DOCUMENTED contract to match the shipped code
(**T9a**, comment/docstring only, zero executable change) and add the one
missing OFFLINE test that exercises the branch (**T9b**). The code was
already correct by design (fail open, per C21); the gap was that nothing
said so precisely enough, and nothing proved it.

**The residual is NAMED, not buried, per C10's discipline.** IF a state
exists where the depth read raises while `ObjectRepository()` and
`usm.Save()` both still succeed at `CurrentDepth > 0`, fail-open proceeds
blind into #243's own incident. None has been found or measured. The one
case the audit checked is non-destructive because `ObjectRepository()`
shares the identical `self.project` dependency and raises FIRST --
established by CODE INSPECTION, not a live probe. Do not upgrade that to
"safe" -- it is "the one checked case is safe," not "the branch is safe."

**On P-11's prediction-before-measurement (QC P1 #2): NO ACTION.** A
git-history proof is impossible because T8b landed as one uncommitted
change with no intermediate commits. The claim instead triangulates from
three independent directions: **C21** froze the 0/25 rollback prediction in
cycle 7, BEFORE the T8b task that measured it ever ran; `/lex-lead`'s own
main session witnessed the prediction stated in the dispatch brief; and the
P-11 test's printed VERDICT branches dynamically on the live count rather
than hardcoding a contradiction string. That is stronger corroboration than
a commit timestamp, which can be amended after the fact.

**FORWARD RULE, not retroactive:** a task that states an a-priori
prediction commits it to a durable artefact (a frozen contract decision, a
dispatch brief, a dynamically-branching assertion) BEFORE the measuring
run, so temporal order is provable from the record for free, without
relying on git history.

**GATE NOTE, recorded not waived:** `lex-qc` is not a registered agent type
in this environment. The cycle-8 QC gate was executed by
`lex-verification` as a read-only claims-vs-evidence audit, and `/lex-lead`
ACCEPTED the substitution at cycle 8 because the gate's content -- P0/P1
findings on the shipped guard, placement, exception type, message accuracy,
test honesty -- was delivered regardless of which agent name ran it.

### C29 -- transaction.py:146-153 is the record's only counter-measurement and gets its own queue line

Ruled 2026-09-07 (spurt 9, cycle 9). The cycle-8 programmer, dispatched to
check `transaction.py` per the brief, found -- and correctly did NOT edit --
a rollback-discards claim at `flexicon/code/transaction.py` lines ~146-153:
a live measurement on the Target sandbox in which a created POS VANISHED on
clean exit under the `helper.RollBack = False` assignment-bug (pythonnet
silently accepting a plain Python attribute write instead of reaching the
private-setter .NET property, so `Dispose()` rolled back every unit of
work, clean ones included).

**RULED: it is a TRUE RECORD of a live measurement and is PROTECTED exactly
as C10's unexplained facts are.** Do not edit it. Do not "reconcile" it
with P-11.

**RULED: it does NOT fold into C25's existing queue bullet.** It is the
record's ONLY counter-measurement -- same mechanism as P-11 (`Dispose()`
with `RollBack` effectively `True`), OPPOSITE outcome (POS vanished vs
25/25 survived). Its value is that it is the single thing preventing a
future reader from generalising P-11 into "rollback never discards." It
therefore gets its OWN bullet in the queue ask, naming the discriminating
variables that were not controlled between the two measurements: object
type (POS vs LexEntry), helper class (`UnitOfWorkHelper` vs
`UndoableUnitOfWorkHelper`), exit path (clean exit vs an escaping
exception), and whether an outer envelope/stack was open at the time. None
of that is resolvable inside #243's scope.

The `docs/TRANSACTION_GUIDE.md` API-Reference gap flagged by the cycle-8
doc agent as outside its authorised scope is ALSO routed to the queue,
gated behind the same C25 ask: its wording depends on that answer, so
writing it now would be guessing.

### C30 -- the pinned 6000-char source-slice window: P2 UPGRADED to a recorded, ungated cleanup, NOT a task in this feature

Ruled 2026-09-07 (spurt 9, cycle 9, at closure). C26 addendum D widened
`tests/test_transaction_honesty.py`'s `save_body` source slice to a magic
`source[save_idx : save_idx + 6000]` and `/lex-lead` logged a P2 at the time:
bound those windows by the next `def ` rather than a magic width. **That P2
bit within one cycle.** T9a's first (accurate) comment draft pushed the
distance from `def SaveChanges(self):` to
`self.ObjectRepository(IUndoStackManager)` from ~5240 to **6589 chars**,
breaking that OFFLINE test -- a file outside T9's scope fence. The
programmer correctly refused to edit out of scope and instead rewrote the
comment more compactly, landing at **5735 chars: a 265-character margin.**

**RULED, on three points.**

1. **The programmer's choice was right and is the precedent.** When an
   in-scope edit breaks an out-of-scope test, rewrite the in-scope edit or
   stop and report -- never widen the scope fence mid-task.

2. **The P2 does NOT become a task in this feature.** Applying this
   record's own decision framework: the defect affects neither #243's
   correctness, nor any public claim, nor the user's ability to trust the
   record. It is test-harness hygiene. Holding a green feature open -- with
   three untouched campaign items that ship data loss today -- for a magic
   number in a test that pins an unrelated invariant (that both methods
   resolve the same accessor) is the wrong prioritisation.

3. **But it does NOT stay a silent P2 in a review file either.** A
   265-char margin is not a margin: the next docstring or comment edit
   anywhere near `SaveChanges()` breaks an unrelated offline test, and the
   pressure that creates is to write a LESS ACCURATE comment to fit a
   test's arbitrary width. In a feature whose entire character has been the
   honesty of its record, leaving that incentive in place is unacceptable.
   It is therefore recorded as an **explicit, UNGATED cleanup bullet** in
   `specs/tier1-silent-data-loss/QUEUE.md` -- deliberately NOT under
   "Awaiting user approval", because it needs no user decision: no
   semantics, no public surface, no live gate (pure test scaffolding, per
   CLAUDE.md's live-verification carve-out).

**The fix, when someone takes it** (~6 lines, with an in-file precedent
20 lines below at `TestOneShotWarningAtOpenProject`, which already bounds
its slice correctly with `source[open_idx:close_idx]`): bound `save_body`
by the index of the next `def ` after `save_idx`, and `refresh_body`
likewise, instead of `+ 6000` / `+ 4000`. **Trigger: do it at the START of
the next spurt that edits `FLExProject.py`'s `SaveChanges()` or
`RefreshFromDisk()` region, before that spurt's own edits.** Do not widen
6000 to 8000 -- that perpetuates the anti-pattern this ruling exists to
end.

**Whoever creates a trap owns defusing it** -- the sibling of C27's
"whoever lands a spurt's docs task owns the sweep". This trap is this
feature's own (C26 addendum D), which is why it leaves here fully
described and pre-ruled rather than as a discovery for the next reader.

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

**RESOLVED 2026-09-07 (spurt 4) as C15.** T3 correctly did NOT decide this
-- its own scope never forced an answer, and as of T3 the `Dispose()` call
is still reached only via the un-guarded `try: ... except Exception: raise`
at `FLExProject.py:333-338`. What forces the answer is **C14**: T7 makes
`CloseProject()` raise after attempting `usm.Save()`, and that raise must
not leak the live LCM handle, so `Dispose()` moves into a `finally`. See
**C15**. Not deferred a fourth time.

**The T4 P-5 measurement (0/25 post-guard) was filed under this heading by
cycle 4 and has been MOVED to Q5.** It does not belong here: Q2 asks what
happens if `usm.Save()` **raises** after the guard runs; the P-5 finding is
the exact complement -- `usm.Save()` does **not** raise and silently
persists nothing. Opposite branch, different remedy. Facts frozen as
**C13**, severity and remedy ruled as **C14**, mechanism routed to **T6**.

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

### Q4 -- CLOSED 2026-09-07 (spurt 8, cycle 8) by `/lex-doc`: placement and wording for P2

**Answer: amend the existing `[Unreleased]` entries in place, not a new
heading, and not a forward pointer off `[4.5.2]`'s `[4.4.0]` history.**
Rationale (one paragraph, per C8's delegation of this call to `/lex-doc`):
`CHANGELOG.md` already carries the #243 story entirely under
`[Unreleased]` -- the `### Changed` section for the public-behaviour
change and the `### Fixed` section for the `CloseProject()` guard -- and
C19/C24 both already establish that editing an as-yet-unreleased entry in
place is zero-churn (nothing published ever changes). A forward pointer
from the shipped `[4.4.0]` entry would scatter one incident's story across
two version blocks for a reader who has not yet seen a release cut, for no
retrievability gain; a brand-new `[Unreleased]` heading would duplicate
the existing `### Changed`/`### Fixed` split for content that belongs
under exactly those headings per Keep-a-Changelog's own category
discipline. The `[4.4.0]` `undoable` default-flip entry is cross-referenced
by *prose* inside the new `### Changed` bullet and the `### Fixed`
paragraph (both name the default flip and its consequence) rather than by
a heading-level pointer, since C8 only requires the cross-reference to
exist, not to take any particular structural form.

### Q5 -- `usm.Save()` returns SUCCESSFULLY having persisted nothing: how must `CloseProject()` detect and report that?

Opened 2026-09-07 (spurt 4, cycle 4) by MOVING the T4 P-5 finding out from
under Q2, where cycle 4 filed it. Q2 is about `usm.Save()` **raising**; this
is the complement -- it returns cleanly and writes nothing. Different
question, opposite branch, different remedy, so it gets its own heading
instead of sharing Q2's.

Already decided and NOT open here: the established facts are frozen as
**C13**; the severity ruling (this is a new silent-loss surface) and the
remedy shape are frozen as **C14**; the internals mechanism was routed to
**T6** and is now frozen as **C16**, with its scope consequence as **C17**.

**The DETECTOR half is RESOLVED 2026-09-07 (spurt 5) as C18.** T6/P-9
measured it: a post-`Save()` `HasUnsavedChanges` read is
**INDISTINGUISHABLE** between a real save and a no-op save, so C14 point 3's
preference for a direct post-save read is **void**. The
Phase-1-envelope-missing anomaly is T7's primary detector; a pre-`Save()`
`HasUnsavedChanges` read is diagnostic-only, must not gate the raise, and
must not be worded as "there is nothing pending to save" (a proven
false-negative). See **C18**.

**Q5 is now FULLY CLOSED.** The paragraph below records the ruling as it
stood while the user's decision was still outstanding (spurts 4-5); it is
kept for history. The user's ruling landed as **C20** (spurt 6): the
`SaveChanges()` guard is approved, and `spec.md` C21-C23 record the shape
that resulted. Read the historical framing below as superseded by C20:

- **Approve the `SaveChanges()` guard** -> the envelope is never collapsed,
  the change set is never discarded, the P-5 chain never forms, the owner's
  sequence can reach 25/25, and C14's raise becomes near-unreachable
  defensive code (still worth having; low-stakes wording).
- **Decline it** -> **C17 makes this branch permanent**: the incident #243
  was filed about becomes unfixable, by measurement and not by choice of
  effort, and T7's ERROR + raise is the *entire* remedy the owner ever
  gets -- so its severity and wording matter a great deal.

**Sharpened by T6 (this is the change the user asked for):** before T6 the
fourth ask read as "would also help". After C16/C17 it is **the only thing
that can fix the filed incident.** The user is no longer deciding whether to
approve an extra improvement; they are deciding whether flexicon fixes #243's
incident at all, or ships #243 documenting it as unfixed.

**One observation for that decision, NOT a new ask and NOT a task.** C16
places the loss *inside* `SaveChanges()`. So even T7's raise reports the loss
**late** -- at close, long after the data went. If the fourth ask is
declined in its "fail fast / prevent" shape, the honest maximum this project
can offer is "loud at close, already lost at `SaveChanges()`". Whether the
same fourth ask should therefore have a *minimum* shape ("at least report
loudly at the point of loss") is part of what the user is deciding about that
one method -- it is **not** a fifth ask, and nothing here may implement,
prototype or plan it. `SaveChanges()` remains untouchable.
