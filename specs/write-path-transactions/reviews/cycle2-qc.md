# QC Report — Track A (write-path-transactions)

**Score: 78/100 — Status: FIX ISSUES**
**Cycle:** 2
**Date:** 2026-08-14

> Persistence note: the lex-qc agent definition grants Read/Grep/Glob only, with no
> write-capable tool, so this report was returned inline and written to this path by
> the orchestrator. Content is the agent's verbatim assessment. Same agent-definition
> gap as lex-domain this cycle; both should be fixed before the next dispatch.

## Pattern-Audit Gate

Gate: **N/A (one-off/feature honesty-pass, justified)**. This is a docstring-honesty
correction (issue #236) plus a new `HeadlessLcmUI` shim (issue #238) — neither matches
the five listed bug shapes (typed-attribute cast, list/sequence assumption, default-arg
semantics, role disambiguation, multilingual-string typing). No commit message was
available since this is uncommitted; confirm with `/lex-programmer` before commit if
`bug`-labelled.

## P0

- **New exception class breaks the FP_* hierarchy convention.**
  `flexicon/code/headless_ui.py:66` defines `FP_ConflictingSaveError(Exception)` directly
  in `headless_ui.py`, not in `flexicon/code/exceptions.py` alongside every other `FP_*`
  type, and it subclasses bare `Exception` rather than `FP_RuntimeError`/`FP_ProjectError`.
  `docs/EXCEPTION_HANDLING.md`'s "Import flexlibs2 Exceptions" list (lines 622-635) was
  not updated to include it. A caller doing `except FP_RuntimeError` (the documented
  pattern) will not catch this new exception. Move it to `exceptions.py`, subclass
  `FP_RuntimeError`, export it from `flexicon/__init__.py`, and add it to the
  exception-hierarchy doc.

## P1

- **Q1 — RefreshFromDisk() write-guard is defensible but not obviously correct.**
  `FLExProject.py:588-589` raises `FP_ReadOnlyError` unconditionally when
  `not self.writeEnabled`. The docstring's own justification ("a read-only session never
  saves, so nothing to unblock") only argues the *auto-save-unblocking* half of the
  method's purpose. But the method's stated purpose is broader — "reconcile in-memory
  state with a foreign change" — and a read-only reporting/monitoring session watching a
  shared project plausibly wants fresh reads without reopening. If
  `IUndoStackManager.Refresh()` is safe/meaningful outside an open UnitOfWork envelope,
  gating it entirely on `writeEnabled` forecloses that caller. Recommend either
  (a) verifying via reflection whether `Refresh()` requires an open envelope and
  loosening the guard if not, or (b) keeping the guard but rewording the docstring to
  state plainly "read-only refresh is out of scope for this cycle" rather than implying
  it is provably unnecessary.

- **Q3 — one test is close to tautological.**
  `tests/test_transaction_honesty.py:87-100`
  (`test_openproject_source_contains_single_warning_call_for_no_rollback_mode`) is a pure
  string/count sweep over the OpenProject source slice. It would catch deletion of the
  warning or duplication of the call, but would NOT catch the warning being emitted with
  wrong content, wrong condition, or moved outside the `writeEnabled and not undoable`
  branch (the test only searches within that already-known branch). The `RollbackToMark`
  sweep in `tests/test_headless_lcm_ui.py:275-286`, by contrast, is a real regression
  catch today (zero current occurrences) but is inherently blind to someone
  reintroducing the same capability under a renamed API — flag this fragility in a
  comment near the test.

- **Q2 — "one-shot" is per-call, not per-process/per-instance, and the docstrings should
  say so explicitly.** `FLExProject.py:256-272`: there is no flag suppressing
  re-emission. A second `OpenProject()` call — same instance reused, or a second
  `FLExProject()` in the same process — re-logs the full warning every time, because
  "one-shot" here means "once per `OpenProject()` invocation, not once per
  `Transaction()` call" (confirmed in `docs/EXCEPTION_HANDLING.md:550-551` and
  `transaction.py:150-153`). That is a reasonable design (each session genuinely
  re-establishes the mode), but the term "one-shot" reads as "only once ever" to a new
  reader. Recommend rewording to "per-session warning" in all three docstrings
  (`FLExProject.py`, `transaction.py`, `BaseOperations.py`), or adding a short note
  explicitly stating it fires again on each `OpenProject()` call.

## P2

- **Q4 — `_TransactionCM` docstring is accurate.** Verified against `transaction.py`'s
  `_NestingAwareTransaction` implementation (depth counter, Phase 2 no-op on nesting,
  Phase 1 never rolls back) — the rewritten docstring (`BaseOperations.py:1767-1845`)
  matches current behavior exactly. No drift found.
- `transaction.py:1-11` file header still says "Class: _FLExTransaction" only; the file
  now defines two classes (`_NestingAwareTransaction` added). Update the header.
- `FLExProject.py` uses inline `logging.getLogger(__name__)` per call site rather than a
  module-level `logger = logging.getLogger(__name__)` (CLAUDE.md convention);
  pre-existing pattern in this file, not introduced by Track A, but the new one-shot
  warning follows the non-canonical pattern too — worth a follow-up cleanup pass, not
  blocking.
- `test_flexlcm_openproject_defaults_to_fwlcmui`
  (`tests/test_headless_lcm_ui.py:195-215`) is a real behavioral test (asserts
  `isinstance(captured["ui"], FwLcmUI)`), not tautological — would fail if the default
  `ui=None` path changed.

## Final Assessment

Recommendation: **FIX ISSUES** — mainly the `FP_ConflictingSaveError` hierarchy
placement (P0) before merge; P1s are documentation/design-clarity items that should be
addressed but do not block on correctness grounds.

**Reviewed By:** QC Agent
