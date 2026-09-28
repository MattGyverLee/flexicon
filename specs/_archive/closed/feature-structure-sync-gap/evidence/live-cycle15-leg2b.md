# Live verification -- Cycle 15, LEG 2b (Checkpoint 4 residual close-out)

**Project:** Target (via `target_sandbox`, tempdir copy of the golden
`.fwbackup`) | **Fixture:** `target_sandbox`
**Command:**
```
export FLEXLIBS_REQUIRE_LIVE=1
python -m pytest "tests/operations/test_grammar_brackets_live.py::TestPOSBrackets" -m requires_live_project -q
```
**run_mode:** live (both sides)
**Date:** 2026-09-07 / 2026-09-08 (session spans local midnight)

## Claim under test

Cycle 14's gate PASSED with zero flips across 90 collected live items in
15 files at both `1d88aa4` (pre-T7) and HEAD, but its enumeration
provably MISSED `tests/operations/test_grammar_brackets_live.py`, the
only live file exercising the POS **write** path
(Delete/SetName/GetName/SetAbbreviation/GetAbbreviation). LEG 2b runs
that file at both commits to close the residual named in cycle 14's
`.crew-handoff.json checkpoint_4.residual_named`.

## AFTER side -- HEAD

Repo state at run time: `2be0651` (branch tip when the command below was
run; a concurrent CHANGELOG-only commit, `9d00826`, landed on `main`
later in the session -- see H4 below. No code file differs between
`2be0651` and `9d00826`, so this result stands for current HEAD.)

```
$ cd D:\Github\_Projects\_LEX\flexicon
$ export FLEXLIBS_REQUIRE_LIVE=1
$ python -m pytest "tests/operations/test_grammar_brackets_live.py::TestPOSBrackets" -m requires_live_project -q
....                                                                     [100%]
[OK] Wrote D:\Github\_Projects\_LEX\flexicon\tests\test_results.json (4 tests recorded)
4 passed, 15 warnings in 5.41s
```

`tests/live_status.json` (HEAD run):
```json
{
  "run_mode": "live",
  "run_timestamp": "2026-09-08T03:23:05Z",
  "by_class": {
    "POSOperations": {
      "delete": {"status": "pass", "tests": ["...test_delete_detaches_from_lcm"]},
      "modify": {"status": "pass", "tests": [
        "...test_setname_round_trips_through_lcm",
        "...test_setabbreviation_round_trips_through_lcm",
        "...test_empty_name_rejected_with_value_unchanged"]}
    }
  },
  "uncategorized_live_tests": []
}
```

## BEFORE side -- 1d88aa4 (disposable worktree)

```
$ git worktree add D:/Github/_Projects/_LEX/flexicon-wt-1d88aa4 1d88aa4
Preparing worktree (detached HEAD 1d88aa4)
HEAD is now at 1d88aa4c docs(feature-structure-sync-gap): commit T7 lead predictions before the run
```

The `.fwbackup` fixture is gitignored (`.gitignore:94`) and therefore not
present in the fresh worktree; it was copied in from the main working
tree's `tests/fixtures/Target 2026-07-06 0218.fwbackup` (same golden
backup used by the HEAD run -- no fixture drift between sides):

```
$ mkdir -p flexicon-wt-1d88aa4/tests/fixtures
$ cp "flexicon/tests/fixtures/Target 2026-07-06 0218.fwbackup" flexicon-wt-1d88aa4/tests/fixtures/
```

```
$ cd D:/Github/_Projects/_LEX/flexicon-wt-1d88aa4
$ export FLEXLIBS_REQUIRE_LIVE=1
$ python -m pytest "tests/operations/test_grammar_brackets_live.py::TestPOSBrackets" -m requires_live_project -q
....                                                                     [100%]
[OK] Wrote D:\Github\_Projects\_LEX\flexicon-wt-1d88aa4\tests\test_results.json (4 tests recorded)
4 passed, 15 warnings in 5.30s
```

`tests/live_status.json` (BEFORE run, same shape, `run_timestamp:
2026-09-08T03:24:04Z`): `"run_mode": "live"`, same four tests recorded
`pass`.

## Cleanup

```
$ git worktree remove --force D:/Github/_Projects/_LEX/flexicon-wt-1d88aa4
$ git worktree prune -v
(silent)
$ git worktree list
D:/Github/_Projects/_LEX/flexicon  9d00826 [main]
```
Only the main worktree remains. `target_sandbox` is a tempdir copy of the
`.fwbackup`, so nothing was written to the real Target; no restore step
was needed. The copied `.fwbackup` in the disposable worktree was
destroyed along with the worktree directory itself.

## H1 verdict -- HELD

4 passed / 4 passed. `run_mode: live` confirmed on both sides (machine
value read from `tests/live_status.json`, not asserted from memory). Zero
flips in either direction. Neither falsifier fired: no GREEN->RED flip
(would have been a P0), and no RED-at-both (no pre-existing failure to
disclaim).

## H2 verdict -- HELD

Alias scan for the pattern `<name> = <something>.POS` across
`tests/operations/*.py`:
```
$ grep -rlE '\w+\s*=\s*\w+(\.\w+)*\.POS\b' tests/operations/
```
found matches in exactly 12 files. Diffed against the gate's 15-file set
(re-extracted from `evidence/live-cycle14-gate.md` lines 154-234; see
`cycle15-verification.md` for the file list): 10 of the 12 are already in
the 15-file set. The 2 outside it are exactly the predicted pair:
`test_grammar_brackets_live.py` (the genuine miss, closed by H1 above)
and `test_issue252_pos_feature_sync.py` (the new T7 file, excluded by
design -- it does not exist at `1d88aa4`). No third file. All 12 matched
files independently confirmed `requires_live_project`-marked.

## H3 verdict -- HELD

```
$ python -m pytest <the 15 gate files> -m requires_live_project --collect-only -q
145/251 tests collected (106 deselected) in 1.69s
```
145 collected, matching the pre-committed prediction exactly. The 15
files were NOT run beyond `TestPOSBrackets` (already covered by the gate
for 90 of 145 plus this leg's 4) -- per the dispatch's explicit
instruction, the remaining ~51 items were not executed this cycle,
because 6 of the 15 files write in-place to a real named FieldWorks
project and doubling that exposure for marginal residual-closing value is
a worse trade than naming it. Named, not run:
`test_msa_kind_and_change_variant.py`, `test_owner_cast_pattern.py`,
`test_pos_catalog.py`, `test_lexsense_operations.py`,
`test_segment_analysis_traversal.py`,
`test_issue251_252_256_feature_struct_probe.py` (partially -- some of its
items were in the 81 already run; the file also opens a named project per
the gate's own risk-profile note) and the unrun remainder of the other 9
files' 145-90=55 total minus this leg's 4 = 51 items.

## H4 verdict -- HELD

`git show 9d00826 -- CHANGELOG.md`: 10 insertions, 0 deletions, 1 file
changed. The added block is a `**Disclosed behaviour change:**` paragraph
inserted directly under the existing `4e9d152`/#252 entry (same
`### ...` heading, no new version heading added), and no pre-existing
line's text changed. Additive only, as predicted.

## Result

**[PASS]** -- H1 HELD (4/4 both commits, live, zero flips), H2 HELD
(exactly 2 files outside the gate's set, no third), H3 HELD (145
collected, matches prediction exactly), H4 HELD (CHANGELOG amendment is
additive-only). Checkpoint 4's residual is closed: the five call sites
`Delete:273, GetName:401, SetName:439, GetAbbreviation:474,
SetAbbreviation:511` now have live evidence at BOTH commits. See
`reviews/cycle15-verification.md` for the full 16-site coverage
statement (which sites remain named-and-not-exercised, and which have
mock-only or zero coverage).
