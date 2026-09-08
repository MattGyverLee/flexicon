# Cycle 15 verification -- LEG 2b (Checkpoint 4 residual)

**Verdict:** [PASS]
**Live run:** yes | **run_mode:** live (both sides, machine-read from
`tests/live_status.json`)
**Evidence:** `specs/feature-structure-sync-gap/evidence/live-cycle15-leg2b.md`
**Project:** Target, via `target_sandbox` (tempdir copy of the golden
`.fwbackup`; sandbox-safe, no in-place writes)

## H1-H4 verdict table

| # | Prediction | Verdict | Basis |
|---|---|---|---|
| H1 (BLOCKING) | `TestPOSBrackets` runs GREEN at both `1d88aa4` and HEAD, zero flips | **HELD** | 4 passed / 4 passed, `run_mode: live` confirmed both sides via `tests/live_status.json`, identical pass pattern, no flip either direction |
| H2 | The alias-pattern miss is singular -- exactly 2 files outside the gate's 15-file set | **HELD** | Independent alias scan found 12 live-marked files matching `= <x>.POS`; 10 already in the 15-file set; the 2 outside are exactly `test_grammar_brackets_live.py` (genuine miss) and `test_issue252_pos_feature_sync.py` (new T7 file, excluded by design, does not exist at `1d88aa4`). No third file. |
| H3 | 15 gate files collect 145 `requires_live_project` items | **HELD** | `--collect-only` across the 15 files: `145/251 tests collected (106 deselected)` -- exact match |
| H4 | CHANGELOG amendment is additive only | **HELD** | `git show 9d00826 -- CHANGELOG.md`: 10 insertions/0 deletions, one paragraph inserted into the existing `4e9d152`/#252 entry, no new heading, no existing line changed |

No falsifier fired for any of the four. Zero P0s, zero P1s.

## P0 / P1 / P2 list

**P0:** none. (H1's falsifier -- a GREEN->RED flip -- did not fire.)
**P1:** none.
**P2:** none new. (H4's item was already fixed by the concurrent
CHANGELOG commit `9d00826`, adjudicated HELD above.)

## The gate's 15-file set (re-extracted, for the record)

From `evidence/live-cycle14-gate.md` lines 154-234, the 81 node-ids span
exactly these 15 files:
`test_abort_session_live.py`, `test_apply_feature_struc.py`,
`test_feature_struc_resolver.py`, `test_issue250_ws_case_divergence.py`,
`test_issue251_252_256_feature_struct_probe.py`,
`test_issue251_msa_feature_sync.py`, `test_lexsense_operations.py`,
`test_makefeatstruc_c3_live.py`, `test_msa_kind_and_change_variant.py`,
`test_owner_cast_pattern.py`, `test_pos_catalog.py`,
`test_pos_operations.py`, `test_segment_analysis_traversal.py`,
`test_set_pos_msa_dispatch.py`, `test_undoable_mode_live.py`.

## Coverage statement -- the 16 pre-existing `__ResolveObject` call sites

Mapping method to line number, per cycle 14's own enumeration in
`POSOperations.py`:

| Call site | Live evidence, BOTH commits? | Basis |
|---|---|---|
| `Delete:273` | **YES** | LEG 2b, this cycle |
| `GetName:401` | **YES** | LEG 2b (read back after `SetName`/guard test) |
| `SetName:439` | **YES** | LEG 2b |
| `GetAbbreviation:474` | **YES** | LEG 2b |
| `SetAbbreviation:511` | **YES** | LEG 2b |
| `GetSubcategories:555` | No -- mock-only, and only `hasattr`-checked, never called with a live object | `test_pos_operations.py::TestPOSOperationsHierarchy::test_has_getsubcategories_method` |
| `AddSubcategory:617` | No -- zero test references anywhere (only a docstring mention in `test_grammar_brackets_live.py`'s `TestPOSBrackets` class docstring, never called) | grep across `tests/` |
| `RemoveSubcategory:673/674` | No -- same as above, docstring-only mention, never called | grep across `tests/` |
| `GetCatalogSourceId:711` | No -- zero test references, mock or live | grep across `tests/` |
| `GetInflectionClasses:751` | No -- zero test references, mock or live | grep across `tests/` |
| `GetAffixSlots:792` | No -- zero test references, mock or live | grep across `tests/` |
| `GetEntryCount:841` | No -- mock-only (`TestGetEntryCount`, patches `GetSubcategories` and a `MockLCMObject`) | `test_pos_operations.py` |
| `Duplicate:913` | No -- zero test references to `POSOperations.Duplicate`; `test_gramcat_duplicate.py` covers the DIFFERENT `GramCatOperations` class, not `POSOperations` | grep + class-definition check (`GramCatOperations.py:32` vs `POSOperations.py:38`) |
| `GetSyncableProperties:1216` | Live at **HEAD only** -- new T7 file `test_issue252_pos_feature_sync.py` does not exist at `1d88aa4`, by design (excluded from LEG 2b per H2/dispatch) | cycle 14 gate condition G7 (6 passed, `run_mode: live`, dated 2026-09-07) |
| `ApplySyncableProperties:1305` | Live at **HEAD only** -- same file, same reason | cycle 14 gate condition G7 |

**Summary:** 5 of 16 sites now have live evidence at BOTH commits
(closed this cycle -- the write-path residual named in cycle 14's
`checkpoint_4.residual_named`). 2 of 16 (`GetSyncableProperties`,
`ApplySyncableProperties`) have live evidence at HEAD only, which is
correct and expected -- they are the T7 change itself and cannot exist
at the pre-T7 commit. The remaining 9 sites are named-and-not-exercised
by any live test at either commit; of those, 2
(`GetSubcategories`, `GetEntryCount`) have mock-only unit coverage and 7
(`AddSubcategory`, `RemoveSubcategory` x2, `GetCatalogSourceId`,
`GetInflectionClasses`, `GetAffixSlots`, `Duplicate`) have **no test
coverage of any kind** referencing those method names -- a finding
surfaced by this leg's coverage audit but out of LEG 2b's scope to fix
(the dispatch bounded this leg to the write-path residual, not a full
POS test-coverage audit).

## Mock suite (regression, supplementary)

Not run this cycle -- out of scope for LEG 2b (dispatch bounded this leg
to H1-H4 only; the mock suite was already run and reported in prior
cycles' verification reports).

## Blockers

None.

## Recommendation

Checkpoint 4's residual is CLOSED: H1 (the blocking prediction) HELD with
zero flips, live-confirmed at both commits via `target_sandbox` (no
in-place project touched). H2-H4 also HELD, no falsifiers fired. The
9-site gap surfaced in the coverage table above (`AddSubcategory`,
`RemoveSubcategory`, `GetCatalogSourceId`, `GetInflectionClasses`,
`GetAffixSlots` with zero coverage; `GetSubcategories`, `GetEntryCount`
with mock-only coverage; `Duplicate` with zero coverage) is a new,
separate, honestly-named residual for the lead to scope as a future task
-- it is NOT part of Checkpoint 4's closing conditions and should not
block closure on it.

APPROVE closure of Checkpoint 4 on H1-H4. The #252 closure comment still
requires the user's own authorisation per standing rules -- no GitHub
action taken this cycle.
