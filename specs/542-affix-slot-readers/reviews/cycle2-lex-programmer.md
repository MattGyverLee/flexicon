# Cycle 2: move #542 live writes off Target, onto a Sena 3 sandbox

## Directive

Binding user directive for this cycle: live write tests may write ONLY to
Sena 3. Nothing may write to the Target project. `restore_target.py` was
not run; Target was never opened write-enabled during this cycle.

## Fixture used

`sena3_sandbox` (preferred option, `tests/flex_plugin.py` ~L1285) --
function-scoped, unzips `tests/fixtures/Sena 3 2026-06-09 1645.fwbackup`
into a fresh tempdir per test, opens it write-enabled
(`writeEnabled=True, undoable=False`), and deletes the tempdir on
teardown. It worked without modification, so the fallback (adding an
in-place `sena3_project` fixture to `flex_plugin.py`) was not needed.

## Fixture file: copied, not moved, and git-ignored

Copied `C:\Github\flexicon\tests\fixtures\Sena 3 2026-06-09 1645.fwbackup`
(source unchanged) into `C:\Github\flexicon-542\tests\fixtures\`. Verified:

```
git check-ignore -v "tests/fixtures/Sena 3 2026-06-09 1645.fwbackup"
.gitignore:98:tests/fixtures/*.fwbackup ...
```

and confirmed via `git status --porcelain` that the file does not appear
as untracked/staged -- it is git-ignored and will not be committed.

## Test file rewrite

`tests/operations/test_issue542_affix_slot_readers_live.py`: replaced
every `target_project` argument with `sena3_sandbox` in all four tests
(`test_slot_readers_round_trip_via_object_and_hvo`,
`test_get_affix_slots_returns_affixslot_wrapper`,
`test_bad_slot_input_raises_parameter_error`,
`test_sena3_affix_slots_are_readable_if_present` -- the last of these
previously opened a second, separate read-only `Sena 3` handle directly;
it now reuses the same sandbox handle already open for the file, since
that project already is Sena 3 and is safe to read). Removed the stale
header comment claiming no `.fwbackup` fixture was present and removed
all mention of Target. Coverage kept identical: object/HVO/wrapper
inputs to `GetSlotName`/`IsSlotOptional`/`GetAffixesInSlot`,
`SetSlotName`/`SetSlotOptional` re-queried from a fresh
`IMoInflAffixSlot(project.Object(hvo))` (never asserting on the value
just passed in), `GetAffixesInSlot` cross-checked against
`MSA.GetInflAffMsaSlots` (#543), `FP_ParameterError` on a non-slot
(`IPartOfSpeech`) input, and the wrapper (`AffixSlot`) round-tripping
into `AddSlotToTemplate`. All created objects keep the `TEST_542_`
prefix and are deleted in `finally:` blocks; because the sandbox is a
disposable tempdir regardless, no leak is possible into any real
project even if a `finally:` block were skipped.

## Test run results

Offline (non-live) gate, run twice -- once with the change, once with
`git stash -u` reverting it, to confirm no regression:

```
python -m pytest -m "not requires_live_project" -q
5 failed, 2506 passed, 1040 deselected, 16 warnings in 11.5s
```

Identical 5 failures both times (`test_lcm_contract.py::...
test_no_new_type_dependencies` and 4 tests in
`test_morphrule_duplicate_deep.py`) -- pre-existing on this branch,
unrelated to this change, not introduced by it.

Live-required run:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue542_affix_slot_readers_live.py -m requires_live_project -q
....
4 passed in 8.59s
```

`tests/live_status.json` after the live run: `"run_mode": "live"`,
`by_class.POSOperations.read.status == "pass"`, all four test IDs listed
under it.

## Evidence

Regenerated `specs/542-affix-slot-readers/evidence/live-542.md`: exact
commands, `run_mode: "live"`, fixture used (`sena3_sandbox`), pre/post
LCM-read-back values for every write (slot name, optional flag, affix
membership, wrapper round-trip through `AddSlotToTemplate`), an explicit
"No writes to Target" section, and the pass/fail line
(`PASS: live-verified`).

## Commit

```
e4f3259 test(grammar): move #542 live writes to a Sena 3 sandbox (#542)
```

New commit on `fix/542-affix-slot-readers` (not amended, not pushed),
2 files changed: the test file and the evidence file.
`Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.

## Answers to the checklist

- Fixture used: `sena3_sandbox` (sandbox/tempdir, preferred option; no
  fallback in-place fixture needed).
- Offline test counts: 2506 passed / 5 failed (pre-existing, both before
  and after this change) / 1040 deselected, both runs.
- Live test counts: 4 passed, 0 failed.
- `run_mode`: `"live"` (confirmed in `tests/live_status.json`).
- Commit SHA: `e4f3259`.
- Fixtures dir git-ignored: yes -- `tests/fixtures/*.fwbackup` matches
  in `.gitignore` line 98; confirmed with `git check-ignore -v` and
  `git status --porcelain` showing no untracked/staged fixture file.
