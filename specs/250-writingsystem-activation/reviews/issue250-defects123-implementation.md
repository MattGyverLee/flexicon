# Issue #250 Defects 1, 2, 3 implementation report

**Task:** Resolve the remaining scope of issue #250 (Defect 4 already
fixed/shipped independently). Defects 1 (`Exists()` contradicts its own
"active only" docstring), 2 (`Create()` conflates store-presence with
usability, refusing to activate an inactive-but-present writing system), and
3 (the resulting silent content drop in `BaseOperations._apply_props_loop`
has no diagnostic) were filed as one interlocking bug and fixed as a set.

## Summary

`WritingSystemOperations.Exists()` now matches `GetAll()`'s active-only
semantics exactly (Defect 1); the whole-store question it used to answer by
accident is preserved under its own name, `ExistsInStore()`. `Create()` no
longer refuses a store-present-but-inactive tag -- it reuses the existing
LDML and only activates it (Defect 2), and a new idempotent
`Ensure(language_tag, name, is_vernacular=True) -> (ws, created)` gives
callers the single-call activate-or-create the issue asked for. The silent
`continue` in `_apply_props_loop` for a genuinely-absent target writing
system now always logs a WARNING naming the property and both the source and
resolved writing-system ids (Defect 3) -- unconditionally, not behind a
`strict=` flag. All three are verified live against `target_sandbox`,
red-then-green (fix reverted and re-applied, each run re-measured), plus 22
new offline unit tests, also confirmed red-then-green.

## Files modified

- `flexicon/code/System/WritingSystemOperations.py`
  - `Exists()`: now intersects `_GetWSByTag()`'s whole-store lookup against
    `_GetAllVernacularWSTags() | _GetAllAnalysisWSTags()`, matching
    `GetAll()`'s own active-set logic exactly. Docstring Notes section
    rewritten to state the active-only scope explicitly and point to
    `ExistsInStore()`/`Ensure()`.
  - `ExistsInStore(language_tag)` (new): the whole-store predicate under its
    own name, body identical to the old `Exists()`.
  - `Create()`: the "already exists" guard is unchanged in *code* (still
    `if self.Exists(language_tag): raise ...`) but is now correctly scoped
    to active tags only, since `Exists()` itself changed. The creation body
    now looks up `existing_ws = self._GetWSByTag(language_tag)` (whole-store)
    first; if found, reuses it (skips `ws_manager.Create()`/`Set()`
    entirely) and only calls `AddToCurrent{Vernacular,Analysis}
    WritingSystems`; only a genuinely-absent tag goes through the original
    `ws_manager.Create()` path. `name` is documented as ignored when reusing
    an existing definition.
  - `Ensure(language_tag, name, is_vernacular=True)` (new): idempotent
    activate-or-create. Returns `(ws, created)` where `created` is `True`
    only for a genuinely new writing system; both "already active" and
    "activated from store" collapse to `created=False` (documented
    divergence from the issue's implied 3-way distinction -- see "Divergence
    from the issue's suggested shape" below). Logs at INFO via
    `logging.getLogger(__name__)` (module-level `logger`, added along with
    `import logging`) for each of the three cases, giving a caller the
    finer distinction if needed.
- `flexicon/code/BaseOperations.py`
  - `_apply_props_loop`: added `import logging` inside the function (module
    precedent already used this local-import style twice elsewhere in this
    same file, e.g. the GUID-fallback warning at `_CreateObjectWithGuid`).
    The `if tgt_handle is None: continue` branch is unchanged in *effect*
    (still drops, still `continue`s) but now precedes the `continue` with
    `logging.getLogger("flexicon").warning(...)` naming `prop_name`,
    `src_ws_id`, `tgt_ws_id`, `type(item).__name__`, and
    `getattr(item, "Hvo", "?")`.

## New test files (uncommitted, per instructions)

- `tests/operations/test_issue250_defects123_ws_activation.py` -- 22 offline
  unit tests (`Mock`-based, no LCM). Every fixture keeps the whole-store
  collection (`all_ws`) and the active-tag collection (`cur_vern_wss`/
  `cur_analysis_wss`) as two genuinely SEPARATE structures -- the issue's
  named trap is a fake that backs both `GetAll()`/`Exists()` off the same
  collection, which makes the divergence unrepresentable. Covers: `Exists()`
  active-only (including a case-divergent-but-inactive case), `ExistsInStore`,
  `Create()`'s reuse-vs-create branching (including a `name`-is-ignored
  check and the zero-regression "already active still raises" case),
  `Ensure()`'s three states plus idempotency plus the "active in the other
  category is added, not moved" rule, and `_apply_props_loop`'s Defect 3
  warning (present on a genuine miss, absent on a hit, and confirmed
  non-raising).
- `tests/operations/test_issue250_defects123_ws_activation_live.py` -- 5 live
  tests against `target_sandbox`, using a helper
  (`_make_store_present_inactive_ws`) that constructs the store-present-but-
  inactive state by creating+activating a genuinely new WS via the public API
  and then removing it *only* from the current (not full) list -- confirmed
  by direct exploration to reproduce exactly the divergence the issue
  describes, without any FieldWorks UI step. All private-use `qaa-x-d250*`
  tags; no dependency on the sandbox's pre-existing `en`/`etu` writing
  systems beyond confirming they're untouched.

## Both test files confirmed red-then-green

Fix reverted via `git apply -R` against a saved diff of exactly the two
source files, both test files re-run, then the diff re-applied:

- Offline: 15 of 22 tests failed pre-fix (the other 7 -- `Exists()`'s
  already-active case, `ExistsInStore`'s already-tested-equivalent-to-old-
  `Exists`, `Create()`'s already-active-raises case, and the two
  Defect-3-does-not-raise/no-warning-on-hit sanity checks -- correctly still
  passed pre-fix, since they exercise behaviour that either didn't change or
  was already correct). Reapplied fix: 22/22 pass.
- Live: 5 of 5 tests failed pre-fix, each for the specific reason predicted
  (`Exists()` still `True` for the inactive tag, `Create()` raising "already
  exists", `Ensure` not existing (`AttributeError`) x2, and no WARNING logged
  for the drop). Reapplied fix: 5/5 pass.

## Per-defect live-verification verdict

All four PASS, `run_mode: live` confirmed on every run. Full detail,
transcripts, and the exploratory transcript proving the store-present-but-
inactive construction works, are in
`specs/250-writingsystem-activation/evidence/live-250-defects123.md`.

| Defect | Verdict |
|---|---|
| 1 (`Exists()` active-only / `ExistsInStore()`) | **PASS (live)**, red-then-green |
| 2 (`Create()` activates instead of refusing) | **PASS (live)**, red-then-green |
| 2 (API gap: `Ensure()`) | **PASS (live)**, red-then-green |
| 3 (silent-drop diagnostics + composition with the Defect 2 fix) | **PASS (live)**, red-then-green |

No `needs_human` blocker was hit -- the store-present-but-inactive state that
the task briefing flagged as possibly requiring FieldWorks' UI was in fact
constructible entirely through the existing public/LCM API (see the evidence
file's exploration transcript).

## Defect 3: warn, not raise -- and why

Chose **an unconditional logged WARNING**, not a raise, for the genuinely
absent case (`_resolve_ws_handle` returning `None` after both exact and
normalized matching fail). Reasoning:

1. **A missing target writing system is not, by itself, an error.**
   Cross-project sync between projects with different writing-system
   coverage is the normal, correct use case this loop exists for (e.g. a
   source project has `es`/`fr` glosses a target project was never meant to
   carry). Making every such partial-overlap sync raise would be a strictly
   worse regression than the silent drop it replaces -- it would fail syncs
   that work correctly today for reasons that have nothing to do with #250.
2. **This is consistent with, not a departure from, the already-loud
   ambiguity case.** `_resolve_ws_handle` (added by Defect 4, #250) already
   raises `FP_ParameterError` when a normalized tag matches two or more
   *distinct* handles (step 2b) -- that is a genuine "the caller's intent is
   undeterminable" situation, categorically different from "the target
   project simply doesn't have this writing system." #266/#267's own loud
   failure mode (also via `_resolve_ws_handle`) is the same ambiguity case,
   not the miss case -- so there is no inconsistency to reconcile: both
   Defect 3 and #266/#267 raise on ambiguity and (for #266, already) drop
   with a diagnostic on a genuine miss.
3. **CLAUDE.md's anti-flag rule cuts the same way.** A `strict=True` kwarg
   whose `False` default preserves the silent drop would be exactly the
   anti-pattern the project's own convention rejects -- "correctness becomes
   the caller's problem." The fix instead makes the CORRECT behaviour
   (observability) unconditional: every caller gets the warning, always, and
   nothing about drop-vs-save changes for any call that already worked.
4. **Pre-validation is genuinely possible now**, which it was not before this
   task: a caller worried about drops can call
   `WritingSystemOperations.Ensure()` for every target tag it cares about
   before syncing, and the log line names exactly which alts still get
   skipped despite that.

## Behaviour changes needing a CHANGELOG entry

All four are recorded in `CHANGELOG.md` under `[Unreleased]`:

- `WritingSystemOperations.Exists()` -- **behaviour change to a public
  predicate** (Defect 1). Swept for internal callers relying on the old
  whole-store semantics (`git grep` for `WritingSystems.Exists` and
  `self.Exists` inside `WritingSystemOperations.py`); the only hit was
  `Create()`'s own guard, addressed by the Defect 2 fix in the same change.
  No other internal caller depends on the old semantics.
- `WritingSystemOperations.Create()` -- behaviour change (no longer raises
  for a store-present-but-inactive tag; activates instead). Documented as a
  bug fix, not a breaking change, since no *currently-succeeding* call
  changes behaviour -- only the previously-always-erroring
  store-present-but-inactive case now succeeds.
- `WritingSystemOperations.ExistsInStore()` -- new public method.
- `WritingSystemOperations.Ensure()` -- new public method, including the
  documented divergence from the issue's implied 3-way return (see below).
- `BaseOperations._apply_props_loop` -- new logging side effect (no
  behavioural/return-value change, but worth recording since it changes
  what appears in logs for existing callers).

## Divergence from the issue's suggested `Ensure()` shape

The issue asked for `Ensure(...) -> (ws, created: bool)` while also asking
that the three input states (already-active / store-present-but-inactive /
genuinely-new) be distinguishable. A 2-element return cannot carry a 3-way
distinction losslessly. I kept the literal 2-tuple signature (explicit
guidance took priority over my own preference for a 3-field return) and
collapsed "already-active" and "activated-from-store" into `created=False`,
because both leave the writing-system *count* unchanged, which is the
operationally relevant fact for the idempotent-pre-pass use case the issue's
own GramTrans example describes (`if tgt_ops.Exists(tag): continue` ->
`Ensure(tag, name)`, called once, trusted to "just work"). The finer 3-way
distinction is preserved at the diagnostic layer instead: `Ensure()` logs one
of three distinct INFO messages (`"already active"`, `"present in store but
inactive; activating"`, `"not present anywhere; creating"`) via
`logging.getLogger("flexicon.code.System.WritingSystemOperations")`, and a
caller that needs it synchronously can call `Exists()` immediately before
`Ensure()` (now correctly active-only, so this composition is finally safe,
which it was not pre-fix). Flagged explicitly here per instructions to
justify any divergence from the issue's proposed fix.

## Follow-ups deliberately left for #266/#267 (NOT filed, NOT acted on)

Per the file-ownership fence, I did not touch `Grammar/PhonemeOperations.py`
or `Lexicon/ExampleOperations.py`. One genuine follow-up surfaced by this
work, for whichever of #266/#267 lands last (or a new issue if both have
already landed by the time this is read):

- **The Defect-3 warning is currently emitted only from
  `BaseOperations._apply_props_loop`.** `#266`'s `PhonemeOperations
  .__ApplyBasicIPASymbol` and `#267`'s `ExampleOperations
  .ApplySyncableProperties` `TranslationsOC` loop each have their own
  independent silent-drop `continue` for a genuinely-absent target writing
  system (this is exactly the resolution-site enumeration #250 Defect 4
  already establishes: 3 sites total). Once those two sites are routed
  through `_resolve_ws_handle` (per C-D4-7, #266 already done, #267 still
  open at time of writing), they will inherit `_resolve_ws_handle`'s
  ambiguity-raise behaviour automatically, but **not** this task's
  miss-case warning, since that warning lives in the caller
  (`_apply_props_loop`), not in `_resolve_ws_handle` itself. If #266/#267's
  own callers want the same observability for a genuine miss, they will
  need their own `logging.getLogger("flexicon").warning(...)` call at their
  own `if tgt_handle is None:` site, mirroring the one added here. I did not
  move the warning into `_resolve_ws_handle` itself, because
  `_resolve_ws_handle` is a pure, project-independent helper (module-level,
  no `self`, spec 250 C-D4-7) and deliberately has no opinion on logging
  policy for its caller's business logic -- only on resolution correctness.
  This is a report-only finding; filing it as an issue needs the user's
  approval per the standing convention in this spec tree.

## Proposed commit subject

```
fix(system): writing-system Exists/Create/Ensure and drop diagnostics for #250 Defects 1-3
```

(No close-keyword immediately before `#250` -- "for #250" rather than
"fix #250"/"resolve #250"/"closes #250". Per the issue's explicit instruction
and the two prior wrongful auto-closes, this issue must NOT be closed by this
commit or any commit referencing it in prose.)
