# T9 QC Review — Issue #326: Phonological Wrapper Members

Reviewer: lex-qc. Worktree `C:/Github/flexicon-326`. Read-only review; no
edits, no commit.

## Score: 96/100

## Block Conditions (P0 gate)

| Condition | Result |
|---|---|
| Missing Pattern Audit in T5 | **PASS** — `T5-programmer.md` contains a full audit table (43 rows) covering all sweep hits with disposition/reason. |
| Missing or mock-mode live evidence in T8 | **PASS** — `evidence/live-T8.md` and `tests/live_status.json` both show `"run_mode": "live"` (re-confirmed independently by running the T5 smoke test myself: `3 passed`). |
| BaseOperations validation / FP_* bypassed on write paths | **PASS** — `PhonologicalRuleOperations.py`'s `Duplicate` (the only touched write path) still routes through `FP_ParameterError`/`FP_ReadOnlyError` and `self._TransactionCM(...)`; unchanged from pre-existing pattern, only comments/messages edited (`PhonologicalRuleOperations.py:1378-1379`). |
| New `flexlibs2` reference | **PASS** — only hit is `CHANGELOG.md`'s prose pointer to the *separate, pre-existing* shim-removal effort ("tracked separately in the main flexlibs2 alias removal"); not a code reference. `test_flexlibs2_alias_ratchet.py` passes (5/5). |

## Verification performed independently

- `git diff main --stat` (16 files, 565+/327-) reviewed in full for the 5 production files.
- `python -m pytest -m "not requires_live_project" -q` → `2043 passed, 5 failed` — **identical 5 test IDs** to T5/T6/T8 (contract-baseline drift + 3 unrelated pre-existing ratchets), confirmed pre-existing not new.
- `pytest.warns` regexes in `tests/test_phonological_rules_wrappers.py` (`has_redup_parts.*deprecated.*v5\.0\.0`, `redup_parts...`, `as_reduplication_rule...`, `redup_rules...`) correctly escape the dot and disambiguate by method name — no cross-matching risk.
- T6 confirmed to have kept all four deprecated symbols (`has_redup_parts`, `redup_parts`, `as_reduplication_rule`, `redup_rules`) with `DeprecationWarning` + v5.0.0 messaging intact — verified directly in the diff, not just T6's self-report.

## P1

None.

## P2 (non-blocking)

1. `flexicon/code/System/phonological_context.py:341,373,428,559` — `from SIL.LCModel import IPhPhoneme`/`IPhNaturalClass` repeated inline 4x instead of once at module/lazy-init scope (style inconsistency vs. `lcm_casting.py`'s `_ensure_interfaces()` pattern). Behaviorally inert; cosmetic only.
2. `tests/operations/test_issue326_t8_verification_live.py` — evidence-only scratch file flagged by T8 itself as needing deletion or folding into the permanent live suite before merge. Not part of this diff's tracked files; housekeeping item for whoever merges.
3. Sena 3 fixture gap (`.fwbackup`/`.fwdata` unusable in this worktree) is disclosed and sanctioned-fallback-covered per T1/T8, but remains an environmental cleanup item outside this task's scope.

## Style / complexity / error handling / test coverage

- New helpers `_is_valid_index_range`, `_get_int_field`, `_metathesis_ranges` in `phonological_rule.py` are small, single-purpose, and each wrapped in `try/except Exception` with `logger.debug(..., exc_info=True)` — consistent with existing wrapper error-handling convention.
- `segment`/`natural_class` use `getattr(..., None)` per T6's simplification, avoiding the `hasattr` double-lookup; behavior-preserving.
- Test coverage is strong: new `TestPhonologicalRuleDeprecation`, `TestPhonologicalRuleMetathesisParts`, `TestPhonologicalContext` classes cover happy path, missing-field, and invalid-range cases offline; live coverage added in `test_phonological_wrappers_live.py` (3 passed) plus T8's independent re-query (2 passed).
- Docstrings and `CHANGELOG.md`/`docs/API_ISSUES_CATEGORIZED.md` updates (T7) match the code's actual behavior (`StrucDescOS` + switch indices, `FeatureStructureRA`).

## Verdict: **APPROVE**
