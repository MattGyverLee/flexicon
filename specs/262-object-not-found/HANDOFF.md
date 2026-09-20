# Handoff -- #262 `FLExProject.Object()` leaks a raw CLR exception

**Branch:** `fix/262-object-stale-guid`
**Status:** ready for review. Implemented, QC-reviewed, and **live-verified**
(`run_mode: live`, 7/7) -- section 4 is discharged; see
`evidence/live-262-verification.md`.
**Baseline:** `49611cc` (main)
**Written:** 2026-09-18 · **Updated:** 2026-09-20

---

## 1. What the issue asked for, and why we did something else

#262 reports that `Object(hvoOrGuid)` has no code path returning `None`: a
malformed guid string raises `FP_ParameterError`, but a **well-formed but
stale** Hvo/Guid leaks a bare CLR
`System.Collections.Generic.KeyNotFoundException` through the wrapper
boundary. Four user scripts across two sessions wrote `if obj is None:`
against it, which never fires.

The issue proposed **returning `None`**. lex-domain **rejected that**, and
the rejection is the load-bearing decision on this branch:

- `Object()` resolves an identity the caller *already holds*. That is a
  different operation from `Find(name)`, and the codebase treats them
  differently. Search-by-criteria returns `None` (e.g.
  `Grammar/POSOperations.py:313-343`, whose docstring says so explicitly).
  Resolve-by-identity **raises** -- every sibling resolver does:
  `Notebook/DataNotebookOperations.py:186-196`,
  `TextsWords/DiscourseOperations.py:136-146, 165-187, 206-217`, and
  `FLExProject.py:3860-3882` (`BuildGotoURL`, which wraps `Object()`
  precisely because `Object()` does not wrap itself).
- `Object()`'s result is routinely fed straight into a write
  (`SetXxx(project.Object(guid), value)`). Returning `None` would turn a
  loud crash into a **silent no-op** -- the Tier-1 silent-data-loss shape
  behind #317 and #318-#321. Today's bug is loud and ugly; `None` would
  make it quiet and wrong. That is a regression, not a fix.
- The apparent counter-example, `BaseOperations.py:2119-2148`
  (`_ResolveFsByGuid`), returns `None` but its own docstring says the
  terminal behaviour should be "a loud `FP_ParameterError` naming the
  GUID" and that its `None` is an internal hand-off. It reinforces the
  ruling.

**Ruling adopted:** catch the CLR exception, re-raise `FP_ParameterError`
naming the id, preserve the original as `__cause__`. Never return `None`.

`Object()` already translated `System.FormatException` two lines above the
bare call -- the intent to wrap was present and simply left incomplete.

## 2. What changed

| File | Change |
|---|---|
| `flexicon/code/FLExProject.py` `Object()` ~3947 | try/except around `ServiceLocator.GetObject`; docstring states the contract and the never-`None` rule |
| `flexicon/code/FLExProject.py` `GetCustomFieldValue()` ~4351, ~4371 | same wrap on the ReferenceAtom and ReferenceCollection possibility lookups |
| `flexicon/code/Lexicon/LexSenseOperations.py` `SetPartOfSpeech()` ~1375, ~1488, ~1516 | same wrap on `pos`, `from_pos`, `to_pos`; the latter two sit inside the open `_TransactionCM`, so an unwrapped leak also aborted a partially-open undo task |
| `docs/EXCEPTION_HANDLING.md` | rewrote the guidance that told users to import `KeyNotFoundException` and catch the raw CLR type around `project.Object(hvo)`; that published contract is wrong as of this change |
| `tests/operations/test_issue262_object_stale_id.py` | new, 15 tests, all offline |

Catch tuple is copied verbatim from the house template at
`DataNotebookOperations.py:186-196`:
`(TypeError, System.InvalidCastException, AttributeError, KeyError,
System.Collections.Generic.KeyNotFoundException)`.

## 3. Pattern audit (required by CLAUDE.md; lex-qc blocks without it)

Shape: *a raw pythonnet/CLR exception escapes the flexicon wrapper boundary
instead of becoming an `FP_*` exception.*

- **Chokepoint.** ~146 call sites of `self.project.Object(` across
  `flexicon/code/` funnel through the one fix in `FLExProject.Object()`,
  including `BaseOperations._GetObject` (1705-1707) and ~50 per-module
  `__ResolveObject` / `__Get*Object` helpers. They are fixed transitively.
- **Tier 1 -- bypass the chokepoint**, so fixed explicitly on this branch:
  the six sites in `GetCustomFieldValue` and `SetPartOfSpeech` listed above.
- **Deliberately out of scope.** Four unguarded `System.Guid(...)` parses
  leak `System.FormatException`, a different exception class:
  `Grammar/PhonFeatureOperations.py:766` and `:958`,
  `Shared/catalog_backed.py:479`,
  `Grammar/InflectionFeatureOperations.py:1496`. All are public-reachable.
  **File these as a follow-up issue; do not widen this PR.**
- **Convention finding.** Wrapping is aspirational, not established: only
  2 of ~60 resolver helpers catch `KeyNotFoundException`, ~15 catch only
  `InvalidCastException`/`AttributeError`, ~45 catch nothing. The
  project-lifecycle boundary (`FLExProject.py:342, 409, 1420`,
  `FLExInit.py:91`) does translate consistently; the object-lookup boundary
  does not. This branch fixes the chokepoint, not the whole gap.

## 4. Live verification -- DISCHARGED 2026-09-20

**PASS.** `tests/live_status.json` shows `"run_mode": "live"`
(`2026-09-20T19:47:25Z`), 7/7 passed. Test file:
`tests/operations/test_issue262_object_stale_id_live.py`. Full evidence:
`evidence/live-262-verification.md`, with the raw captured CLR data in
`evidence/live-262-probes-raw.json`.

    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest tests/operations/test_issue262_object_stale_id_live.py -m requires_live_project -q

Run against `target_sandbox` (a tempdir copy); the machine-shared Target
project was never touched.

**The load-bearing result:** the CLR type is
`System.Collections.Generic.KeyNotFoundException` for every stale-id form,
*and* for `Hvo=0`, `Hvo=-1` and a random foreign Guid. Nothing escaped the
catch tuple as `ArgumentException`, `OverflowException`, or anything else,
so the production `except` clause is correctly specified rather than
merely assumed. Probe 5 confirmed the cascade-delete pattern in
`test_wfi_analysis.py` still works, its broad `except Exception:` catching
`FP_ParameterError` as it previously caught the raw CLR type.

The probes, as originally specified by lex-domain and all now discharged:

1. Create an object, capture `.Guid` and `.Hvo`, delete it, then call
   `Object(guid_str)`, `Object(System.Guid(...))` and `Object(hvo_int)` on
   the stale id. Confirm the CLR type is `KeyNotFoundException` in all
   three, and capture the MRO -- the except clause depends on it.
2. A/B a *never-existed* very large Hvo against the *deleted* case above and
   confirm the exception type is identical. Prior evidence covers each
   separately but never in one controlled run.
3. Edge inputs with no prior evidence: `Hvo=0`, a negative int, and an
   Hvo/Guid valid in a *different* project open in the same process.
   Confirm none produces `ArgumentException` / `OverflowException` or
   anything else that would slip past the catch tuple.
4. Confirm the valid case is unchanged: `Object(hvo)` / `Object(guid)`
   round-trip still returns the correct `ICmObject`.
5. **Regression risk.** `tests/operations/test_wfi_analysis.py` relies on
   `Object()` raising for a deleted HVO as its cascade-delete "gone" signal
   (see `specs/291-swallowed-assert/evidence/live-291-cascade.md:36-53`).
   Its `except Exception:` should still catch `FP_ParameterError`, but
   confirm it rather than assume.

### lex-qc review -- DISCHARGED 2026-09-20

Verdict: **APPROVE WITH CHANGES**. Both required changes are applied.

1. **ReferenceAtom repository hoist.** The `GetCustomFieldValue`
   ReferenceAtom branch evaluated the whole
   `self.ObjectRepository(ICmPossibilityRepository).GetObject(item)` chain
   inside the `try`, so an `AttributeError` from a broken service-locator
   chain would have been relabelled as a failed item lookup. The
   repository resolution is now hoisted out, matching what the
   ReferenceCollection branch two cases below already did.
2. **CHANGELOG entry** for the behavioural divergence from upstream.

The two queued questions were answered:

- *Catch-tuple breadth* (`TypeError`/`AttributeError`): accepted for
  house-template consistency. Every site preserves `__cause__` via
  `from e` and inlines the original message, so a mislabelled error is
  still diagnosable -- mislabelled, not swallowed.
- *Factoring the duplicated tuple into a helper*: **declined.**
  Copy-paste is the established convention here -- the same five-line
  block is already duplicated four times in `DiscourseOperations.py` and
  `DataNotebookOperations.py` before this branch. Migrating only the six
  new sites would leave a worse mixed state, and CLAUDE.md forbids
  introducing an abstraction that is not already house convention. If it
  is ever done, it should be one sweep across all ten sites.

Left alone as cosmetic: `docs/EXCEPTION_HANDLING.md:432,438,474` still
show generic `except KeyNotFoundException` snippets, but they illustrate
non-`Object()` call sites and sit beside a correctly-updated example.

## 5. Upstream parity

`cdfarrow/flexlibs` `Object()` is byte-for-byte identical to this repo's
pre-fix version, so the bug is **inherited, not introduced**, and this repo
has not previously diverged on this method. The fix is therefore a
deliberate, disclosed divergence: post-fix, `flexicon.Object()` raises
`FP_ParameterError` where `flexlibs.Object()` still leaks the CLR type.
Call it out in CHANGELOG.md, and note it near the migration/compat
discussion, so a user moving between the two libraries is not surprised.

## 6. Where the work lives

Committed on `fix/262-object-stale-guid`. It was developed in the isolated
worktree `C:\Github\flexicon-bugfix-loop` because the main checkout at
`C:\Github\flexicon` had concurrent uncommitted edits from another session.
The worktree is disposable once the branch is pushed:

    git -C C:/Github/flexicon worktree remove ../flexicon-bugfix-loop

Note the worktree needed `tests/fixtures/Target*.fwbackup` copied in by
hand -- it is gitignored, so a fresh worktree does not inherit it and the
live suite fails loudly without it.
