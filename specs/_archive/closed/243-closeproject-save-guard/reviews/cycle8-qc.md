# Cycle 8 -- QC audit: T8b SaveChanges() depth guard

**Score: 90/100**
**P0 count: 0**

## P1

1. **Fail-open catch is broader than its own justification (FLExProject.py:846-859).**
   The guard does `except Exception as e: depth = 0`, but C4/C21's reasoning
   only covers ONE documented raise: `FP_ProjectError` when `self.project`
   doesn't exist. I verified that case is safe by code inspection --
   `ObjectRepository()` (line 3498: `self.project.ServiceLocator.GetService(...)`)
   has the identical `self.project` dependency, so on a closed/never-opened
   project it raises `AttributeError` one line before `usm.Save()` is ever
   reached (line 888-889) -- non-destructive, matches the reasoning given.
   But the code catches *any* exception from the depth read, not just
   `FP_ProjectError`, and no test -- live or offline -- exercises this
   fail-open branch at all (grepped both live test files, zero hits). The
   "both need self.project" argument is sound for the one case checked; it
   is unverified for any other exception `ActionHandlerAccessor.CurrentDepth`
   could throw on a live but degraded project object. Not a P0 because no
   concrete destructive counterexample exists or was found -- but it is an
   unverified breadth-of-catch mismatch on new write-path code, which this
   agent's charter treats seriously.

2. **Audit instruction 5(b) (prove prediction predates measurement) cannot be
   fully satisfied from this diff.** All of T8b landed as one uncommitted
   change with no intermediate commits, so `git diff` cannot show temporal
   order of docstring-vs-run. The strongest available evidence is external
   to the test file: spec.md C21 (frozen in cycle 7, before the T8b
   programmer task ran) already states the 0/25 rollback prediction as a
   "caveat to record, not resolved here," and the P-11 test's own printed
   VERDICT branches dynamically on the live count rather than hardcoding
   the contradiction string. Taken together this is good practice and I
   found no sign of retuning, but it falls short of a git-history proof.

## P2

- `flexicon/code/FLExProject.py.backup` exists in the tree (untracked
  artifact, likely editor/tool residue) -- not part of this diff's claims
  but worth someone's cleanup pass.

## Findings by question

1. **Fail-open policy** -- see P1 #1. No realistic destructive counterexample
   found; reasoning holds for the one documented raise, unverified for others.
2. **Message accuracy** -- CONFIRMED. `undoable=False` message
   (FLExProject.py:873-886) matches P-10 case C / P-5 measured basis (25/25
   in-memory AND on-disk). `undoable=True` message (862-871) says only
   "commits automatically when it exits normally" -- scoped to the normal-exit
   path P-10 case A measured, says nothing about an escaping exception, so
   P-11's contradictory finding does not falsify it. No overclaim in either.
3. **Exception type** -- CONFIRMED correct and consistent.
   `FP_TransactionError` matches the identical depth-refusal pattern at
   `CustomFieldOperations.py:306-307`, is used by `undoable_operation.py:96`
   and `AbortSession()`'s own depth-based refusals, and is importable both
   as `from .FLExProject import FP_TransactionError` (imported at
   FLExProject.py:34) and from top-level `flexicon` (`__init__.py:97`).
4. **Guard placement** -- CONFIRMED. Guard runs at FLExProject.py:841-886,
   strictly after `if not self.writeEnabled` (841) and strictly before the
   sole `usm = self.ObjectRepository(IUndoStackManager)` / `usm.Save()` at
   888-889. Grepped the whole file for `.Save()` call sites: only two exist
   (CloseProject() line 433, guarded by T7/C23; SaveChanges() line 889,
   guarded by T8b) -- no bypass path.
5. **Test honesty**:
   (a) CONFIRMED genuine. Read P-7's body: it now calls the raw
   `project.ObjectRepository(IUndoStackManager)` + `usm.Save()` accessor and
   still asserts the literal `"Commit at wrong place."` string and the 0/25
   in-memory count -- unweakened, still a real liblcm-mechanism probe.
   (b) Prediction-vs-measurement contradiction is prominently documented in
   the P-11 docstring and assertion messages; see P1 #2 for the one
   limitation on proving temporal order.
6. **Docstrings** -- CONFIRMED accurate. `RefreshFromDisk()`'s note
   explicitly states the unmeasured boundary ("has not been measured here
   and is not claimed") per C10 discipline; `AbortSession()`'s example
   routes to `CloseProject()`, not `SaveChanges()`, with correct inline
   reasoning.

## Recommendation
APPROVE, with the two P1s logged for a follow-up (not blocking): add a live
or offline test for the fail-open branch, and narrow the `except Exception`
to what's actually justified (or explicitly broaden the documented contract
to match it).
