# Issue #542 live evidence (cycle 3: contract regen + CreateAffixSlot wrapper return)

## Why this supersedes the cycle-2 evidence

Cycle 2's evidence covered the read-side methods (`GetSlotName`,
`IsSlotOptional`, `SetSlotName`, `SetSlotOptional`, `GetAffixesInSlot`,
`GetAffixSlots`) against the Sena 3 sandbox. Cycle 3 adds:

1. A regenerated `tests/contract/snapshots/expected_contract.json` (the
   `IMoInflAffixSlot` import from `affix_slot.py`/`POSOperations.py` was
   missing from the baseline, failing
   `TestContractStability::test_no_new_type_dependencies` on this branch).
2. `POSOperations.CreateAffixSlot` now returns an `AffixSlot` wrapper
   instead of the raw `IMoInflAffixSlot` (domain must-fix, Rule 3).
3. A new live test, `test_create_affix_slot_returns_affixslot_wrapper`,
   proving the wrapper round-trips through `AddSlotToTemplate` and
   `SetInflAffMsaSlots`, with every claim re-queried from the LCM.

Per the same binding user directive as cycle 2, live write tests in this
cycle wrote ONLY to the Sena 3 sandbox (`sena3_sandbox` fixture). No test
using `target_project` or `target_sandbox` was run; Target was never
opened write-enabled; no restore script was run.

## Environment

FieldWorks 9 is installed on this runner
(`C:\Program Files\SIL\FieldWorks 9\`), so `SIL.LCModel` loads as the real
.NET assembly for the whole pytest session (liblcm version `11.0.0.0`,
informational version
`11.0.0-beta.173+Branch.master.Sha.8f855bc14ce36446ee2254544ed2f6fa98dff618`).

## Command (exact, as run)

```
cd C:\Github\flexicon-542
python -m pytest -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue542_affix_slot_readers_live.py -m requires_live_project -q
```

(Bash-tool equivalents used in this session: `export FLEXLIBS_REQUIRE_LIVE=1`.)

## Contract snapshot regeneration

Regenerated with the sanctioned tool:

```
python -m tests.contract.extract_lcm_contract -o tests/contract/snapshots/expected_contract.json
```

`git diff` on the result contains ONLY the additions this branch
introduced: `IMoInflAffixSlot` added to the `SIL.LCModel` import list and
to the top-level type-usage list, a new `code/Grammar/affix_slot.py` file
entry, `IMoInflAffixSlot` added to `Lexicon/POSOperations.py`'s import
list, and the summary counts incrementing by exactly one
(`total_files_with_lcm_deps` 81->82, `total_unique_imports` 269->270,
`total_interfaces` 112->113). No unrelated drift.

`tests/contract/snapshots/liblcm_baseline.json` (the Mode-2 live
reflection snapshot) was regenerated wholesale first
(`python -m tests.contract.generate_lcm_snapshot -o
tests/contract/snapshots/liblcm_baseline.json`) to confirm
`IMoInflAffixSlot` really exists on the installed liblcm -- it does
(`types.IMoInflAffixSlot.found == True`, with `Name`/`Optional`/`Affixes`
present, matching `affix_slot.py`'s assumptions). That wholesale
regeneration pulled in ~1950 lines of unrelated drift (the installed
liblcm moved from beta.161, 2026-09-08, the previous baseline's
generation date, to beta.173, 2026-09-26 -- a live environment two weeks
newer than the last commit touching this file). Per instruction, the
wholesale regeneration was discarded and only the new
`IMoInflAffixSlot` type entry was hand-inserted into the existing
`liblcm_baseline.json`, in the same alphabetical position the tool would
have placed it (between `IMoInflAffMsaFactory` and `IMoInflAffixTemplate`).
`git diff --stat` on the result: `1 file changed, 123 insertions(+)` --
exactly the one new type entry, nothing else.

## Result

Contract tests:

```
python -m pytest tests/contract -q -m "not requires_live_project"
23 passed, 2 warnings in 1.34s
```

(A prior run without the snapshot fix: `1 failed, 22 passed` --
`test_no_new_type_dependencies` reporting `+ IMoInflAffixSlot` as an
undeclared new dependency. Confirmed fixed.)

Full offline (non-live) run:

```
python -m pytest -m "not requires_live_project" -q
4 failed, 2507 passed, 1041 deselected, 16 warnings in 11.20s
```

The 4 failures are pre-existing and unrelated to this change, all in
`tests/operations/test_morphrule_duplicate_deep.py::TestDuplicateDeepGating`
(`test_default_call_does_not_raise_nameerror`,
`test_deep_false_does_not_copy_slot_references`,
`test_deep_true_copies_slot_references`,
`test_deep_true_keyword_matches_docstring_example`) -- the exact set named
as the expected baseline for this task. No regression from the
`CreateAffixSlot` wrapper-return change or the contract snapshot update.

Live run:

```
python -m pytest tests/operations/test_issue542_affix_slot_readers_live.py -m requires_live_project -q
.....
5 passed in 9.90s
```

Five tests (one more than cycle 2's four): the new
`test_create_affix_slot_returns_affixslot_wrapper` plus the four carried
over from cycle 2.

## run_mode

`tests/live_status.json` after the live run:

```json
"run_mode": "live",
"run_timestamp": "2026-09-26T23:11:18Z"
```

`by_class.POSOperations.add.status` = `"pass"`
(`test_create_affix_slot_returns_affixslot_wrapper`).
`by_class.POSOperations.read.status` = `"pass"`, all four cycle-2 tests
listed.

## Pre-state / post-state read back from the LCM

Test `test_create_affix_slot_returns_affixslot_wrapper` (Sena 3 sandbox,
new this cycle):

| Step | Read back via | Value |
|---|---|---|
| `CreateAffixSlot(pos, "TEST_542_create_slot", optional=True)` | `type(slot)` | `AffixSlot` (not a raw `IMoInflAffixSlot`) |
| Same | `slot.name` / `slot.optional` (wrapper properties, proxied) | `"TEST_542_create_slot"` / `True` |
| Wrapper passed directly to `AddSlotToTemplate(template, slot, "prefix")` | Fresh `IMoInflAffixTemplate` re-fetched via `IPartOfSpeech(project.Object(pos_hvo)).AffixTemplatesOS`, then `.PrefixSlotsRS` HVOs | `slot_hvo` present in the re-fetched sequence (not the value passed in -- a fresh lookup from the owning POS) |
| Wrapper passed directly to `MSA.SetInflAffMsaSlots(sense, [slot], replace=True)` | `MSA.GetInflAffMsaSlots(sense)` (independent read-side method, #543's inverse lookup) | `{slot_hvo}` |

Cycle-2 tests re-verified unchanged this cycle (see cycle-2 evidence
retained in git history for the full pre/post table);
`test_slot_readers_round_trip_via_object_and_hvo`,
`test_get_affix_slots_returns_affixslot_wrapper`,
`test_bad_slot_input_raises_parameter_error`, and
`test_sena3_affix_slots_are_readable_if_present` all still pass unchanged
by this cycle's edits.

## Cleanup

`test_create_affix_slot_returns_affixslot_wrapper` deletes its created
`TEST_542_create_pos` entry and POS in a `finally:` block. Because all
writes went to a tempdir sandbox (`sena3_sandbox`) that is deleted on
fixture teardown regardless, no cleanup can leak into a real project even
if the `finally:` block were skipped.

## No writes to Target

Confirmed: `test_issue542_affix_slot_readers_live.py` does not import or
reference `target_project` or `target_sandbox` anywhere. The only project
handle opened by any test in this file is `sena3_sandbox`, a disposable
tempdir copy. `test_issue255_affix_slot_live.py` and
`test_issue258_set_infl_aff_msa_slots_live.py` (both `target_sandbox`,
edited this cycle only to keep their assertions correct against the new
`AffixSlot`-wrapper return of `CreateAffixSlot`) were NOT run, per the
binding user directive. The real Target project
(`C:\ProgramData\SIL\FieldWorks\Projects\Target\Target.fwdata`) was not
opened write-enabled at any point during this verification.
`scripts/restore_target.py` was not run. `scripts/restore_sena3.py` was
not run either -- `sena3_sandbox` is a disposable tempdir copy, not the
real Sena 3 project.

## Pass/fail

**PASS: live-verified.** `run_mode: "live"`, both required invocations
run, pre/post LCM state re-queried (not just asserted against the value
passed in) for the new wrapper-return behavior, contract snapshot
regenerated and confirmed to introduce no unrelated drift, all writes
confined to a Sena 3 sandbox tempdir, zero writes to Target,
`target_sandbox` tests not run per user directive.
