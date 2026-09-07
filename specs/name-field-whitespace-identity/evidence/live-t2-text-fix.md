# Name-field whitespace identity -- T2 (TextOperations persist + comparison-symmetry fix), live evidence

**Scope (per `tasks.md` T2 / `spec.md` C1-C5, C8):**
`flexicon/code/TextsWords/TextOperations.py`, three sites, re-confirmed at
HEAD by symbol lookup immediately before editing (no drift from the task
brief's line numbers this cycle):

- `Create` (`:151-152`) -- `_ValidateStringNotEmpty(name, "text name")` at
  `:151` STAYS unchanged. Remove the rebinding `name = name.strip()` at
  `:152` so `TsStringUtils.MakeString(name, wsHandle)` at `:170` persists
  the caller's original, unstripped argument. `self.Exists(name)` at
  `:155` now receives the RAW name -- correct and safe once `Exists`
  strips both sides of its own comparison (below).
- `Exists` (`:457-464`) -- `_ValidateStringNotEmpty(name, "text name")` at
  `:457` STAYS. Remove the rebinding `name = name.strip()` at `:458`.
  Strip INLINE at both comparison sides instead, per C4's exact shape,
  `casefold=False` preserved unchanged:
  ```
  target = normalize_match_key(name, casefold=False).strip()
  ...
  if normalize_match_key(text_name, casefold=False).strip() == target:
  ```
- `SetName` (`:606-609`) -- `_ValidateParam(name, "name")` at `:606` STAYS.
  The existing shape is `_ValidateParam` -> `name = name.strip()` -> a
  SECOND `_ValidateParam(name, "name")` at `:609`. Per C7(b), SetName's
  `AttributeError`-on-non-str behaviour (raised today by `.strip()` itself,
  since `_ValidateParam` is a null-check only -- confirmed by reading
  `BaseOperations.py:2747-2796`, which documents "Lightweight null check"
  with no `isinstance` branch) is explicitly OUT OF SCOPE (belongs to
  Q-242C) and must NOT change type. Simply deleting the `.strip()` call
  entirely (as T1 did for `DiscourseOperations`) would REMOVE that
  `AttributeError` trigger for a non-str payload, since there `_ValidateStringNotEmpty`
  already type-checks upstream and `TextOperations.SetName` has no
  equivalent guard. To preserve the exact existing exception shape while
  still not rebinding `name`, the fix keeps the `.strip()` CALL as a
  throwaway (discarding its result, not reassigning `name`):
  ```
  self._ValidateParam(name, "name")

  name.strip()  # throwaway: still raises AttributeError for a non-str
                # payload (C7(b) -- exception TYPE unchanged), but no
                # longer rebinds `name`, so the persist below writes the
                # caller's original argument.
  self._ValidateParam(name, "name")
  ```
  This is a deliberate, documented DEVIATION in mechanism (not in outcome)
  from T1's "just delete the line" shape, driven by C7(b)'s binding
  constraint that SetName's non-str exception type must not change. It is
  recorded here as a CONTRACT CONTRADICTIONS FOUND item if T3/T4 copy this
  file's shape naively without checking whether their own sites have an
  upstream type-check already (they do, via `_ValidateStringNotEmpty` for
  `CheckOperations`, but `AnthropologyOperations.Create`/`CreateSubitem`
  are explicitly EXCLUDED from harmonisation per C7(b) and are not part of
  T3's persist-only scope in the same way -- T3 must check its own sites'
  shape independently, not copy this mechanically).

No shared file (`BaseOperations.py`, `Shared/string_utils.py`) touched.
No new comparison method added; `Exists` is the only comparison site in
scope for T2 (per `tasks.md` T2, `Find` at `:507-517` is NOT listed and is
NOT touched).

## OFFLINE BASELINE, BEFORE THE EDIT

Command: `python -m pytest tests -m "not requires_live_project" -q`

```
3 failed, 1292 passed, 501 deselected, 12 warnings in 14.59s
```

Matches `CONCURRENCY.md`'s expected red baseline exactly (three named
known-foreign failures, `deselected` already reflects T1's +3 landed
tests):
`test_transaction_rollback.py::TestPhase2JoinOrOpen::test_rollback_flag_set_true_on_exception`,
`::test_depth_restored_on_exception`,
`test_flexlibs2_alias_ratchet.py::...::test_no_executable_flexlibs2_imports_outside_alias_package`.
No fourth failure. `git status --porcelain` shows only the other crew's
known/attributed files (`.claude/ralph-loop.local.md` deleted,
`specs/feature-structure-sync-gap/{STATUS.md,spec.md}` modified,
`specs/name-field-whitespace-identity/CONCURRENCY.md` modified by the
main session per its own header, `.vscode/` and
`specs/duplicate-signature-harmonisation/` untracked/attributed,
`specs/feature-structure-sync-gap/{evidence,reviews}/*T4*` untracked/theirs) --
none of these are staged by this task.

## PREDICTIONS (committed BEFORE the live measuring run; C28 forward rule --
not edited after the fact even if a prediction misses)

- **T2-P1 (Create persist byte-identical):** `Texts.Create("TEST_NF_...  ")`
  (trailing space) is **PREDICTED** to persist the text's `Name` re-read
  from the LCM (`ITsString(text.Name.BestAnalysisAlternative).Text`) as
  byte-identical to the caller's original argument, because
  `TsStringUtils.MakeString(name, wsHandle)` at `:170` now runs against the
  unmodified parameter.

- **T2-P2 (SetName persist byte-identical):** `Texts.SetName(text,
  "TEST_NF_... ")` (trailing space) is **PREDICTED** to persist the text's
  `Name` re-read from the LCM as byte-identical to the caller's argument,
  same mechanism, via the throwaway-`.strip()` shape above.

- **T2-P3 (Exists comparison symmetry -- PN2 flip):** Once a name is
  persisted WITH its trailing space intact (via the fixed `Create`),
  `Exists(<unpadded needle>)` and `Exists(<padded needle>)` are BOTH
  **PREDICTED** to return `True` -- the opposite of PN2's pre-fix
  assertion (which required both to be `False`, proving needle-only
  stripping). Post-fix, both sides of the comparison are stripped inline,
  so a padded or unpadded needle matches a padded haystack symmetrically.

- **T2-P4 (duplicate rejection -- PN8 flip, THE C8 pin):**
  `Texts.Create(<name with trailing space>)` called TWICE is **PREDICTED**:
  the first call succeeds and persists the padded name byte-identically;
  the SECOND call is **PREDICTED to RAISE** `FP_ParameterError` ("already
  exists"), because `Exists()` now strips both sides and finds the
  first record's padded name as a match for the second call's
  (identically padded) needle. This is the opposite of the pre-fix PN8
  result (duplicate succeeded).

- **T2-P5 (C2's prediction on byte-identity of both records, re-tested):**
  `spec.md` C2 predicts that once C4's persist fix lands, "both records in
  this scenario would be persisted from the caller's original, unstripped
  argument and would be byte-identical." Under T2-P4 above, there is only
  ONE record (the second `Create` call is predicted to RAISE, not persist
  a second record) -- so C2's specific "both records byte-identical"
  scenario cannot arise post-fix for `TextOperations`, because the
  duplicate that C2 was describing is EXACTLY what C4's comparison-symmetry
  fix prevents. This is **PREDICTED** to be confirmed as a natural
  consequence, not a contradiction: C2 was describing the PRE-fix
  intermediate state (persist fixed, comparison not yet fixed) to justify
  why persist-only is insufficient; T2 lands persist AND comparison
  together (per C5), so that intermediate state is never reached in
  practice by the shipped code. The PN8 test is extended to assert the
  fixed (rejecting) behaviour, with the pre-fix "duplicate succeeds,
  non-byte-identical second record" behaviour preserved as a comment for
  the historical record.

- **T2-P6 (whitespace-only rejection unaffected):** `Create("   ")` is
  **PREDICTED** to still raise `FP_ParameterError` via the unchanged
  `_ValidateStringNotEmpty` call at `:151`. `Exists("   ")` is likewise
  **PREDICTED** to raise the same, via `:457`, before ever computing a
  `target`. This confirms the binding-constraint note (no defensive empty-
  target guard needed in `Exists` -- whitespace-only is rejected upstream).

## Test file

`tests/operations/test_name_field_identity_probe.py` -- EXTENDED in place
(PN2 and PN8 flipped to assert fixed behaviour, per `tasks.md` T2; no
parallel probe file created).

## Fixtures

`target_sandbox` / `target_sandbox_path` ONLY. Never the real Target,
never `scripts/restore_*.py`.
